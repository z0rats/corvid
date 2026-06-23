import base64
import logging
import mimetypes
from io import BytesIO

import exifread
from PIL import Image, UnidentifiedImageError

from ..schemas.image_schemas import GpsInfo, ImageAnalysisResponse, ImageFileInfo
from ..utils.hash_utils import calculate_image_hashes

logger = logging.getLogger(__name__)

# exifread tags that hold raw embedded thumbnail bytes rather than readable values
THUMBNAIL_TAGS = {'JPEGThumbnail', 'TIFFThumbnail'}


def _ratio_to_float(value) -> float:
    """Convert an exifread Ratio (or plain number) to a float."""
    num = getattr(value, "num", None)
    den = getattr(value, "den", None)
    if num is not None and den is not None:
        return num / den if den else 0.0
    return float(value)


def _dms_to_decimal(dms_values, ref: str | None) -> float:
    """Convert EXIF GPS degrees/minutes/seconds values to decimal degrees."""
    degrees, minutes, seconds = (_ratio_to_float(v) for v in dms_values)
    decimal = degrees + minutes / 60 + seconds / 3600
    if ref and ref.upper() in ('S', 'W'):
        decimal = -decimal
    return decimal


def _extract_file_info(filename: str, data: bytes) -> ImageFileInfo:
    """Extract basic file properties using Pillow."""
    image = Image.open(BytesIO(data))
    dpi = image.info.get('dpi')
    dpi_x, dpi_y = dpi if dpi else (None, None)
    mime_type, _ = mimetypes.guess_type(filename)

    return ImageFileInfo(
        filename=filename,
        format=image.format,
        mime_type=mime_type,
        width=image.width,
        height=image.height,
        mode=image.mode,
        dpi_x=float(dpi_x) if dpi_x else None,
        dpi_y=float(dpi_y) if dpi_y else None,
        file_size=len(data),
    )


def _extract_exif_tags(data: bytes) -> dict:
    """Extract all readable EXIF/IPTC/XMP tags using exifread."""
    try:
        return exifread.process_file(BytesIO(data), details=True)
    except Exception as e:
        logger.warning("Error reading EXIF tags: %s", e)
        return {}


def _extract_gps(tags: dict) -> GpsInfo | None:
    """Build a GpsInfo object from exifread GPS tags, if present."""
    lat_tag = tags.get('GPS GPSLatitude')
    lon_tag = tags.get('GPS GPSLongitude')
    if not lat_tag or not lon_tag:
        return None

    try:
        lat_ref = str(tags.get('GPS GPSLatitudeRef')) if tags.get('GPS GPSLatitudeRef') else 'N'
        lon_ref = str(tags.get('GPS GPSLongitudeRef')) if tags.get('GPS GPSLongitudeRef') else 'E'
        latitude = _dms_to_decimal(lat_tag.values, lat_ref)
        longitude = _dms_to_decimal(lon_tag.values, lon_ref)

        altitude = None
        alt_tag = tags.get('GPS GPSAltitude')
        if alt_tag and alt_tag.values:
            altitude = _ratio_to_float(alt_tag.values[0])

        return GpsInfo(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            map_url=f"https://www.google.com/maps?q={latitude},{longitude}",
        )
    except Exception as e:
        logger.warning("Error parsing GPS tags: %s", e)
        return None


def _extract_thumbnail(tags: dict) -> str | None:
    """Return a base64 data URI for the embedded EXIF thumbnail, if present."""
    thumbnail_bytes = tags.get('JPEGThumbnail')
    if not thumbnail_bytes or not isinstance(thumbnail_bytes, bytes):
        return None
    encoded = base64.b64encode(thumbnail_bytes).decode('ascii')
    return f"data:image/jpeg;base64,{encoded}"


def analyze_image_content(filename: str, data: bytes) -> ImageAnalysisResponse:
    """Analyze image data and return comprehensive metadata.

    Raises ValueError if the file is not a readable image.
    """
    logger.info("Starting image analysis for %s byte file", len(data))

    try:
        file_info = _extract_file_info(filename, data)
    except UnidentifiedImageError as e:
        raise ValueError("File is not a recognized image format") from e

    hashes = calculate_image_hashes(data)
    raw_tags = _extract_exif_tags(data)

    exif = {
        str(tag_name): str(tag_value)
        for tag_name, tag_value in raw_tags.items()
        if tag_name not in THUMBNAIL_TAGS
    }
    gps = _extract_gps(raw_tags)
    thumbnail_base64 = _extract_thumbnail(raw_tags)

    logger.info(
        "Image analysis completed - %s EXIF tags, GPS: %s, thumbnail: %s",
        len(exif), bool(gps), bool(thumbnail_base64)
    )

    return ImageAnalysisResponse(
        file_info=file_info,
        hashes=hashes,
        exif=exif,
        gps=gps,
        has_thumbnail=thumbnail_base64 is not None,
        thumbnail_base64=thumbnail_base64,
    )
