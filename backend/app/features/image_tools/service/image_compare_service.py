"""Field-by-field comparison of two images: EXIF/IPTC/XMP tags plus a perceptual-hash
distance to indicate whether the underlying pixel content is likely the same.

Reuses analyze_image_content for each side rather than re-implementing EXIF
extraction and pHash computation - the same trusted extraction logic on both
images guarantees a fair diff.
"""

import logging

from ..utils.phash_utils import hamming_distance
from .image_metadata_service import analyze_image_content
from ..schemas.image_schemas import FieldDiff, FieldDiffSummary, ImageCompareResponse

logger = logging.getLogger(__name__)

PIXEL_MATCH_THRESHOLD = 10  # Hamming distance out of 64 bits


def _diff_exif_fields(left_exif: dict, right_exif: dict) -> list[FieldDiff]:
    all_fields = sorted(set(left_exif) | set(right_exif))
    diffs = []
    for field in all_fields:
        left_value = left_exif.get(field)
        right_value = right_exif.get(field)
        if left_value is not None and right_value is not None:
            status = "match" if left_value == right_value else "differ"
        elif left_value is not None:
            status = "only_left"
        else:
            status = "only_right"
        diffs.append(FieldDiff(field=field, left_value=left_value, right_value=right_value, status=status))
    return diffs


def _summarize(diffs: list[FieldDiff]) -> FieldDiffSummary:
    return FieldDiffSummary(
        match_count=sum(1 for d in diffs if d.status == "match"),
        differ_count=sum(1 for d in diffs if d.status == "differ"),
        only_left_count=sum(1 for d in diffs if d.status == "only_left"),
        only_right_count=sum(1 for d in diffs if d.status == "only_right"),
    )


def compare_images(left_filename: str, left_data: bytes, right_filename: str, right_data: bytes) -> ImageCompareResponse:
    """Compare two images. Raises ValueError if either file isn't a readable image."""
    left = analyze_image_content(left_filename, left_data)
    right = analyze_image_content(right_filename, right_data)

    diffs = _diff_exif_fields(left.exif, right.exif)
    summary = _summarize(diffs)

    distance = hamming_distance(int(left.phash.hex, 16), int(right.phash.hex, 16))

    logger.info(
        "Compared '%s' vs '%s': %s match, %s differ, phash distance %s",
        left_filename, right_filename, summary.match_count, summary.differ_count, distance,
    )

    return ImageCompareResponse(
        left=left.file_info,
        right=right.file_info,
        field_diffs=diffs,
        summary=summary,
        phash_distance=distance,
        pixels_likely_match=distance <= PIXEL_MATCH_THRESHOLD,
    )
