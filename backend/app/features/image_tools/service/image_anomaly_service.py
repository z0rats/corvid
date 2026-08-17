"""Heuristic tampering/anomaly detection.

Runs a handful of independent forensic checks and reports whatever they find -
none of these are proof of tampering on their own, just signals worth a closer
look (same caveat any tool like this has to carry). EXIF/timestamp/software
checks work on any format exifread can read; the JPEG-only checks (trailing
data, marker order, quantization consistency) are skipped for other formats.
"""

import logging
from datetime import datetime, timedelta
from io import BytesIO

import exifread
from PIL import Image

from ..schemas.image_schemas import AnomalyFinding, ImageAnomalyResponse
from ..utils.jpeg_markers import TRAILING_DATA, walk_markers
from ..utils.phash_utils import compute_phash, hamming_distance
from .image_structure_service import get_quantization_tables

logger = logging.getLogger(__name__)

EXIF_DATETIME_TAGS = ["EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"]
TIMESTAMP_DRIFT_THRESHOLD = timedelta(days=1)

# GPS time is UTC while EXIF capture time is usually local, so this needs a much
# more generous margin than TIMESTAMP_DRIFT_THRESHOLD to absorb any timezone
# offset (max +/-14h) without flagging normal photos.
GPS_TIMESTAMP_DRIFT_THRESHOLD = timedelta(days=2)

# Substrings matched case-insensitively against the EXIF Software tag.
EDITING_SOFTWARE_SIGNATURES = [
    "photoshop",
    "lightroom",
    "gimp",
    "snapseed",
    "picsart",
    "affinity photo",
    "paint.net",
    "capture one",
    "luminar",
    "pixelmator",
    "canva",
    "vsco",
]

THUMBNAIL_MISMATCH_THRESHOLD = 10  # Hamming distance out of 64 bits

QUANTIZATION_QUALITY_SPREAD_THRESHOLD = 20  # percentage points between table estimates


def _parse_exif_datetime(value) -> datetime | None:
    try:
        return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
    except ValueError, TypeError:
        return None


def _check_timestamp_consistency(tags: dict) -> AnomalyFinding | None:
    parsed = {}
    for tag_name in EXIF_DATETIME_TAGS:
        tag = tags.get(tag_name)
        if tag is None:
            continue
        dt = _parse_exif_datetime(tag)
        if dt:
            parsed[tag_name] = dt

    if len(parsed) < 2:
        return None

    spread = max(parsed.values()) - min(parsed.values())
    if spread <= TIMESTAMP_DRIFT_THRESHOLD:
        return None

    detail = ", ".join(f"{name}={dt.isoformat()}" for name, dt in parsed.items())
    return AnomalyFinding(
        check="timestamp_consistency",
        severity="warning",
        message=f"EXIF timestamps disagree by {spread} ({detail})",
    )


def _ratio_to_float(value) -> float:
    num = getattr(value, "num", None)
    den = getattr(value, "den", None)
    if num is not None and den is not None:
        return num / den if den else 0.0
    return float(value)


def _parse_gps_datetime(tags: dict) -> datetime | None:
    """Combine GPS GPSDate + GPSTimeStamp (both UTC) into one datetime.

    exifread names the GPSDateStamp EXIF tag (0x1D) "GPS GPSDate", not
    "GPS GPSDateStamp" - verified against its actual output, not just the spec.
    """
    date_tag = tags.get("GPS GPSDate")
    time_tag = tags.get("GPS GPSTimeStamp")
    if not date_tag or not time_tag:
        return None

    try:
        year, month, day = (int(part) for part in str(date_tag).replace("-", ":").split(":"))
        hour, minute, second = (int(_ratio_to_float(v)) for v in time_tag.values)
        return datetime(year, month, day, hour, minute, second)
    except ValueError, TypeError, AttributeError:
        return None


def _check_gps_timestamp_consistency(tags: dict) -> AnomalyFinding | None:
    gps_dt = _parse_gps_datetime(tags)
    if gps_dt is None:
        return None

    capture_tag = tags.get("EXIF DateTimeOriginal")
    if capture_tag is None:
        return None
    capture_dt = _parse_exif_datetime(capture_tag)
    if capture_dt is None:
        return None

    spread = abs(gps_dt - capture_dt)
    if spread <= GPS_TIMESTAMP_DRIFT_THRESHOLD:
        return None

    return AnomalyFinding(
        check="gps_timestamp_mismatch",
        severity="warning",
        message=f"GPS timestamp ({gps_dt.isoformat()} UTC) differs from the EXIF capture time "
        f"({capture_dt.isoformat()}) by {spread} - more than a timezone offset alone would explain",
    )


def _check_editing_software(tags: dict) -> AnomalyFinding | None:
    software = tags.get("Image Software") or tags.get("EXIF Software")
    if not software:
        return None

    value = str(software)
    lowered = value.lower()
    if any(signature in lowered for signature in EDITING_SOFTWARE_SIGNATURES):
        return AnomalyFinding(
            check="editing_software",
            severity="warning",
            message=f"Editing software fingerprint found in EXIF: '{value}'",
        )
    return None


def _check_thumbnail_mismatch(main_image: Image.Image, tags: dict) -> AnomalyFinding | None:
    thumbnail_bytes = tags.get("JPEGThumbnail")
    if not thumbnail_bytes or not isinstance(thumbnail_bytes, bytes):
        return None

    try:
        thumbnail_image = Image.open(BytesIO(thumbnail_bytes))
    except Exception as e:
        logger.warning("Could not decode embedded thumbnail for mismatch check: %s", e)
        return None

    distance = hamming_distance(compute_phash(main_image), compute_phash(thumbnail_image))
    if distance <= THUMBNAIL_MISMATCH_THRESHOLD:
        return None

    return AnomalyFinding(
        check="thumbnail_mismatch",
        severity="warning",
        message=f"Embedded thumbnail differs significantly from the main image (hash distance "
        f"{distance}/64) - the image may have been edited after the thumbnail was generated",
    )


def _check_trailing_data(markers) -> AnomalyFinding | None:
    trailing = next((m for m in markers if m.code == TRAILING_DATA), None)
    if not trailing or not trailing.length:
        return None
    return AnomalyFinding(
        check="trailing_data",
        severity="warning",
        message=f"{trailing.length} bytes found after the JPEG end marker (EOI) - "
        "could be an appended file, steganography, or file corruption",
    )


def _check_marker_order(markers) -> AnomalyFinding | None:
    issues = []
    soi_count = sum(1 for m in markers if m.code == 0xD8)
    if soi_count != 1:
        issues.append(f"expected exactly one SOI marker, found {soi_count}")
    if not any(m.code == 0xD9 for m in markers):
        issues.append("no EOI marker found")

    if not issues:
        return None
    return AnomalyFinding(check="marker_order", severity="warning", message="; ".join(issues))


def _check_quantization_consistency(data: bytes) -> AnomalyFinding | None:
    try:
        tables = get_quantization_tables(data)
    except ValueError:
        return None

    estimates = [t.quality_estimate for t in tables if t.quality_estimate is not None]
    if len(estimates) < 2:
        return None

    spread = max(estimates) - min(estimates)
    if spread <= QUANTIZATION_QUALITY_SPREAD_THRESHOLD:
        return None

    return AnomalyFinding(
        check="quantization_tables",
        severity="warning",
        message=f"Quantization tables imply inconsistent quality across channels "
        f"({min(estimates)}-{max(estimates)}%) - unusual for direct camera output, often seen "
        "after re-encoding/editing",
    )


def analyze_image_anomalies(filename: str, data: bytes) -> ImageAnomalyResponse:
    """Run all applicable anomaly checks against an image file.

    Raises ValueError if the file isn't a recognizable image at all.
    """
    try:
        main_image = Image.open(BytesIO(data))
        main_image.load()
    except Exception as e:
        raise ValueError("File is not a recognized image format") from e

    try:
        raw_tags = exifread.process_file(BytesIO(data), details=True)
    except Exception as e:
        logger.warning("Error reading EXIF tags for anomaly detection: %s", e)
        raw_tags = {}

    findings: list[AnomalyFinding] = []
    checks = [
        _check_timestamp_consistency(raw_tags),
        _check_gps_timestamp_consistency(raw_tags),
        _check_editing_software(raw_tags),
        _check_thumbnail_mismatch(main_image, raw_tags),
    ]

    is_jpeg = len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8
    if is_jpeg:
        markers = walk_markers(data)
        checks.extend(
            [
                _check_trailing_data(markers),
                _check_marker_order(markers),
                _check_quantization_consistency(data),
            ]
        )

    checks_run = len(checks)
    findings = [finding for finding in checks if finding is not None]

    logger.info(
        "Anomaly detection for '%s': %s/%s checks flagged something",
        filename,
        len(findings),
        checks_run,
    )

    return ImageAnomalyResponse(filename=filename, findings=findings, checks_run=checks_run)
