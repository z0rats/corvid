"""Lossless EXIF/metadata removal for JPEG, with a best-effort fallback for other formats.

For JPEG, cleaning is done at the marker level (see utils/jpeg_markers.py):
metadata-carrying segments are dropped or patched in place while SOI/DQT/DHT/
SOF/SOS/EOI and the entropy-coded pixel data are re-emitted byte-for-byte
untouched - "location_only" mode never changes any segment's length, so no
offset recalculation is ever needed when reassembling the file.
"""

import io
import logging
from typing import Literal

from PIL import Image

from ..utils.jpeg_markers import SCAN_DATA, TRAILING_DATA, RawMarker, serialize_markers, walk_markers

logger = logging.getLogger(__name__)

_APP1 = 0xE1
_APP13 = 0xED
_COM = 0xFE
_EXIF_PREFIX = b"Exif\x00\x00"

_GPS_IFD_TAG = 0x8825
_TIFF_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}


def _zero_gps_ifd(app1_payload: bytes) -> bytes:
    """Zero out the GPS IFD (pointer + its entries + any out-of-line data) within an EXIF APP1 payload.

    In-place only: every write stays within the existing byte layout, so the
    payload's length never changes and no other IFD offset needs adjusting.
    Leaves all non-GPS EXIF tags (camera, timestamps, software, ...) intact.
    """
    if not app1_payload.startswith(_EXIF_PREFIX):
        return app1_payload

    tiff_start = len(_EXIF_PREFIX)
    buf = bytearray(app1_payload)
    if len(buf) < tiff_start + 8:
        return bytes(buf)

    byte_order = bytes(buf[tiff_start:tiff_start + 2])
    if byte_order == b"II":
        endian = "little"
    elif byte_order == b"MM":
        endian = "big"
    else:
        return bytes(buf)  # not a valid TIFF header, leave untouched

    def u16(offset: int) -> int:
        return int.from_bytes(buf[offset:offset + 2], endian)

    def u32(offset: int) -> int:
        return int.from_bytes(buf[offset:offset + 4], endian)

    def set_u32(offset: int, value: int) -> None:
        buf[offset:offset + 4] = value.to_bytes(4, endian)

    ifd0_offset = tiff_start + u32(tiff_start + 4)
    if ifd0_offset + 2 > len(buf):
        return bytes(buf)

    entry_count = u16(ifd0_offset)
    entries_start = ifd0_offset + 2

    for i in range(entry_count):
        entry_offset = entries_start + i * 12
        if entry_offset + 12 > len(buf):
            break
        if u16(entry_offset) != _GPS_IFD_TAG or u16(entry_offset + 2) != 4:  # tag, type (LONG)
            continue

        gps_ifd_offset = tiff_start + u32(entry_offset + 8)

        if gps_ifd_offset + 2 > len(buf):
            buf[entry_offset:entry_offset + 12] = b"\x00" * 12
            break
        gps_count = u16(gps_ifd_offset)
        gps_entries_start = gps_ifd_offset + 2

        # Zero any out-of-line data (e.g. RATIONAL lat/lon/altitude values, which
        # don't fit in the 4-byte inline value field) before the entries table
        # that stores those offsets gets wiped below.
        for j in range(gps_count):
            gps_entry_offset = gps_entries_start + j * 12
            if gps_entry_offset + 12 > len(buf):
                break
            g_type = u16(gps_entry_offset + 2)
            g_count = u32(gps_entry_offset + 4)
            size = _TIFF_TYPE_SIZES.get(g_type, 1) * g_count
            if size > 4:
                data_offset = tiff_start + u32(gps_entry_offset + 8)
                if data_offset + size <= len(buf):
                    buf[data_offset:data_offset + size] = b"\x00" * size

        gps_ifd_total_len = 2 + gps_count * 12 + 4  # count + entries + next-IFD offset
        end = min(gps_ifd_offset + gps_ifd_total_len, len(buf))
        buf[gps_ifd_offset:end] = b"\x00" * (end - gps_ifd_offset)

        # Zero the IFD0 entry itself (tag/type/count/value) last, now that we're
        # done reading its value - readers key lookups by tag id, so a zeroed
        # tag field makes this entry invisible to GPS-tag lookups entirely,
        # while the fixed 12-byte slot keeps IFD0's entry count/layout valid.
        buf[entry_offset:entry_offset + 12] = b"\x00" * 12
        break  # only one GPS IFD pointer expected in IFD0

    return bytes(buf)


def _strip_jpeg_markers(data: bytes, mode: Literal["all", "location_only"]) -> bytes:
    markers = walk_markers(data)
    kept: list[RawMarker] = []

    for marker in markers:
        if marker.code == TRAILING_DATA:
            continue  # bytes appended after EOI are never metadata we want to keep

        if marker.code == _APP1:  # EXIF and/or XMP
            if mode == "all":
                continue
            if marker.payload.startswith(_EXIF_PREFIX):
                kept.append(RawMarker(
                    code=marker.code,
                    offset=marker.offset,
                    length=marker.length,
                    payload=_zero_gps_ifd(marker.payload),
                ))
            else:
                kept.append(marker)  # XMP-only APP1: no EXIF GPS IFD to strip
            continue

        if marker.code in (_APP13, _COM) and mode == "all":
            continue

        kept.append(marker)

    return serialize_markers(kept)


def _strip_other_format(data: bytes) -> tuple[bytes, str]:
    """Best-effort metadata strip for non-JPEG formats via a clean Pillow re-encode.

    Rebuilding the image from raw pixel bytes guarantees no ancillary
    chunks/tags survive, regardless of format-specific metadata quirks -
    unlike JPEG this isn't guaranteed byte-identical to the original.
    """
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as e:
        raise ValueError("File is not a recognized image format") from e

    clean_image = Image.frombytes(image.mode, image.size, image.tobytes())
    buf = io.BytesIO()
    fmt = image.format or "PNG"
    clean_image.save(buf, format=fmt)
    return buf.getvalue(), f"image/{fmt.lower()}"


def strip_metadata(filename: str, data: bytes, mode: Literal["all", "location_only"]) -> tuple[bytes, str, str]:
    """Remove metadata from an image file.

    Returns (cleaned_bytes, media_type, output_filename). Raises ValueError
    for corrupt/unparseable input.
    """
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        out_filename = f"{stem}_cleaned.{ext}"
    else:
        out_filename = f"{filename}_cleaned"

    is_jpeg = len(data) >= 2 and data[0] == 0xFF and data[1] == 0xD8
    if is_jpeg:
        cleaned = _strip_jpeg_markers(data, mode)
        logger.info("Stripped JPEG metadata (mode=%s) for '%s': %s -> %s bytes", mode, filename, len(data), len(cleaned))
        return cleaned, "image/jpeg", out_filename

    cleaned, media_type = _strip_other_format(data)
    logger.info("Stripped non-JPEG metadata for '%s': %s -> %s bytes", filename, len(data), len(cleaned))
    return cleaned, media_type, out_filename
