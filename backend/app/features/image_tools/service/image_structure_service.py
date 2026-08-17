"""JPEG structure and quality analysis - marker map, quantization/Huffman tables, frame info.

Built entirely on the byte-level parsing in utils/jpeg_markers.py, independent
of Pillow/exifread (which are used by image_metadata_service for EXIF/file info).
"""

import logging

from ..schemas.image_schemas import (
    FrameComponent,
    FrameInfo,
    HuffmanTable,
    ImageStructureResponse,
    MarkerSegment,
    QuantizationTable,
)
from ..utils.jpeg_markers import SCAN_DATA, TRAILING_DATA, RawMarker, marker_name, walk_markers

logger = logging.getLogger(__name__)

HEX_PREVIEW_BYTES = 256

# Standard IJG quantization tables at quality=50 (JPEG Annex K / libjpeg
# jcparam.c std_luminance_quant_tbl / std_chrominance_quant_tbl), natural
# (row-major) order. Used as the baseline to estimate save quality.
_STD_LUMINANCE = [
    16,
    11,
    10,
    16,
    24,
    40,
    51,
    61,
    12,
    12,
    14,
    19,
    26,
    58,
    60,
    55,
    14,
    13,
    16,
    24,
    40,
    57,
    69,
    56,
    14,
    17,
    22,
    29,
    51,
    87,
    80,
    62,
    18,
    22,
    37,
    56,
    68,
    109,
    103,
    77,
    24,
    35,
    55,
    64,
    81,
    104,
    113,
    92,
    49,
    64,
    78,
    87,
    103,
    121,
    120,
    101,
    72,
    92,
    95,
    98,
    112,
    100,
    103,
    99,
]
_STD_CHROMINANCE = [
    17,
    18,
    24,
    47,
    99,
    99,
    99,
    99,
    18,
    21,
    26,
    66,
    99,
    99,
    99,
    99,
    24,
    26,
    56,
    99,
    99,
    99,
    99,
    99,
    47,
    66,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
    99,
]

# Standard JPEG zigzag scan order: ZIGZAG_ORDER[i] is the natural (row-major)
# index of the i-th value read from a DQT segment.
_ZIGZAG_ORDER = [
    0,
    1,
    8,
    16,
    9,
    2,
    3,
    10,
    17,
    24,
    32,
    25,
    18,
    11,
    4,
    5,
    12,
    19,
    26,
    33,
    40,
    48,
    41,
    34,
    27,
    20,
    13,
    6,
    7,
    14,
    21,
    28,
    35,
    42,
    49,
    56,
    57,
    50,
    43,
    36,
    29,
    22,
    15,
    23,
    30,
    37,
    44,
    51,
    58,
    59,
    52,
    45,
    38,
    31,
    39,
    46,
    53,
    60,
    61,
    54,
    47,
    55,
    62,
    63,
]

_SOF_CODES = {c for c in range(0xC0, 0xD0) if c not in (0xC4, 0xC8, 0xCC)}


def _dezigzag(values: list[int]) -> list[int]:
    natural = [0] * 64
    for zigzag_index, natural_index in enumerate(_ZIGZAG_ORDER):
        natural[natural_index] = values[zigzag_index]
    return natural


def _estimate_quality(values: list[int], standard: list[int]) -> int | None:
    """Estimate JPEG save quality (1-100) using the standard IJG scaling-factor inversion."""
    ratios = [v * 100 / s for v, s in zip(values, standard, strict=False) if s]
    if not ratios:
        return None
    scale = sum(ratios) / len(ratios)
    quality = (200 - scale) / 2 if scale <= 100 else 5000 / scale
    return max(1, min(100, round(quality)))


def _to_marker_segment(marker: RawMarker) -> MarkerSegment:
    if marker.code in (SCAN_DATA, TRAILING_DATA):
        return MarkerSegment(
            marker_type=marker_name(marker.code),
            offset=marker.offset,
            length=marker.length,
        )

    raw_hex = None
    truncated = False
    if marker.payload:
        preview = marker.payload[:HEX_PREVIEW_BYTES]
        raw_hex = preview.hex()
        truncated = len(marker.payload) > HEX_PREVIEW_BYTES

    return MarkerSegment(
        marker_type=marker_name(marker.code),
        marker_code=f"0x{marker.code:02X}",
        offset=marker.offset,
        length=marker.length,
        raw_hex=raw_hex,
        truncated=truncated,
    )


def _parse_quantization_tables(markers: list[RawMarker]) -> list[QuantizationTable]:
    tables = []
    for marker in markers:
        if marker.code != 0xDB:
            continue
        payload = marker.payload
        pos = 0
        while pos < len(payload):
            precision = 16 if (payload[pos] >> 4) else 8
            table_id = payload[pos] & 0x0F
            pos += 1
            value_count = 64 * (2 if precision == 16 else 1)
            if pos + value_count > len(payload):
                break
            if precision == 16:
                zigzag_values = [
                    int.from_bytes(payload[pos + 2 * i : pos + 2 * i + 2], "big") for i in range(64)
                ]
            else:
                zigzag_values = list(payload[pos : pos + 64])
            pos += value_count

            natural_values = _dezigzag(zigzag_values)
            standard = _STD_LUMINANCE if table_id == 0 else _STD_CHROMINANCE
            tables.append(
                QuantizationTable(
                    table_id=table_id,
                    precision=precision,
                    values=natural_values,
                    quality_estimate=_estimate_quality(natural_values, standard),
                )
            )
    return tables


def _parse_huffman_tables(markers: list[RawMarker]) -> list[HuffmanTable]:
    tables = []
    for marker in markers:
        if marker.code != 0xC4:
            continue
        payload = marker.payload
        pos = 0
        while pos < len(payload):
            table_class = "AC" if (payload[pos] >> 4) else "DC"
            table_id = payload[pos] & 0x0F
            pos += 1
            if pos + 16 > len(payload):
                break
            code_lengths = list(payload[pos : pos + 16])
            pos += 16
            total_codes = sum(code_lengths)
            pos = min(pos + total_codes, len(payload))
            tables.append(
                HuffmanTable(
                    table_class=table_class,
                    table_id=table_id,
                    code_lengths=code_lengths,
                    total_codes=total_codes,
                )
            )
    return tables


def _derive_chroma_subsampling(components: list[FrameComponent]) -> str:
    if len(components) < 3:
        return "N/A"

    y, cb, cr = components[0], components[1], components[2]
    if (cb.horizontal_sampling, cb.vertical_sampling) != (
        cr.horizontal_sampling,
        cr.vertical_sampling,
    ):
        return "custom"
    if cb.horizontal_sampling == 0 or cb.vertical_sampling == 0:
        return "custom"

    h_ratio = y.horizontal_sampling / cb.horizontal_sampling
    v_ratio = y.vertical_sampling / cb.vertical_sampling
    if h_ratio == 1 and v_ratio == 1:
        return "4:4:4"
    if h_ratio == 2 and v_ratio == 1:
        return "4:2:2"
    if h_ratio == 2 and v_ratio == 2:
        return "4:2:0"
    return "custom"


def _parse_frame(markers: list[RawMarker]) -> FrameInfo | None:
    for marker in markers:
        if marker.code not in _SOF_CODES:
            continue
        payload = marker.payload
        if len(payload) < 6:
            return None

        precision = payload[0]
        height = (payload[1] << 8) | payload[2]
        width = (payload[3] << 8) | payload[4]
        num_components = payload[5]

        components = []
        pos = 6
        for _ in range(num_components):
            if pos + 3 > len(payload):
                break
            sampling = payload[pos + 1]
            components.append(
                FrameComponent(
                    component_id=payload[pos],
                    horizontal_sampling=sampling >> 4,
                    vertical_sampling=sampling & 0x0F,
                    quantization_table_id=payload[pos + 2],
                )
            )
            pos += 3

        is_progressive = marker.code == 0xC2
        kind = (
            "Baseline"
            if marker.code == 0xC0
            else "Progressive"
            if is_progressive
            else "Extended Sequential"
            if marker.code == 0xC1
            else marker_name(marker.code)
        )

        return FrameInfo(
            frame_type=f"{kind} ({marker_name(marker.code)})",
            is_progressive=is_progressive,
            precision=precision,
            width=width,
            height=height,
            components=components,
            chroma_subsampling=_derive_chroma_subsampling(components),
        )
    return None


def get_quantization_tables(data: bytes) -> list[QuantizationTable]:
    """Public entry point for reuse by other services (e.g. anomaly detection) that
    only need the quantization tables/quality estimates, not a full structure report.

    Raises ValueError if `data` isn't a valid JPEG (see walk_markers).
    """
    return _parse_quantization_tables(walk_markers(data))


def analyze_jpeg_structure(filename: str, data: bytes) -> ImageStructureResponse:
    """Analyze the byte-level structure of a JPEG file.

    Raises ValueError if the file isn't a valid/complete JPEG (not JPEG at
    all, or missing a frame header).
    """
    markers = walk_markers(data)

    frame = _parse_frame(markers)
    if frame is None:
        raise ValueError("No frame header (SOF) found - not a complete JPEG file")

    quantization_tables = _parse_quantization_tables(markers)
    huffman_tables = _parse_huffman_tables(markers)

    estimates = [t.quality_estimate for t in quantization_tables if t.quality_estimate is not None]
    overall_quality_estimate = round(sum(estimates) / len(estimates)) if estimates else None

    compression_ratio = None
    bits_per_pixel = None
    pixel_count = frame.width * frame.height
    if pixel_count:
        compression_ratio = round((pixel_count * 3) / len(data), 2)
        bits_per_pixel = round((len(data) * 8) / pixel_count, 3)

    logger.info(
        "Structure analysis completed for %s - %s markers, %s DQT, %s DHT, quality~%s",
        filename,
        len(markers),
        len(quantization_tables),
        len(huffman_tables),
        overall_quality_estimate,
    )

    return ImageStructureResponse(
        filename=filename,
        file_size=len(data),
        markers=[_to_marker_segment(m) for m in markers],
        quantization_tables=quantization_tables,
        huffman_tables=huffman_tables,
        frame=frame,
        overall_quality_estimate=overall_quality_estimate,
        compression_ratio=compression_ratio,
        bits_per_pixel=bits_per_pixel,
    )
