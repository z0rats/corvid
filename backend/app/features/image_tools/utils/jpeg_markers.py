"""Byte-level JPEG marker segment walker.

Shared by image_structure_service (interprets markers for display) and
image_metadata_removal_service (rebuilds the file dropping selected markers).
Every marker's payload/length is left untouched when reconstructing a file
from a filtered marker list, so pixel data is never re-encoded.
"""

from dataclasses import dataclass

# Sentinel "codes" for byte ranges that aren't a marker segment themselves but
# still need to be represented in the ordered marker list so callers can
# locate/preserve them. Outside the 0x00-0xFF marker byte range so they can
# never collide with a real marker code.
SCAN_DATA = 0x100      # entropy-coded scan data following an SOS segment
TRAILING_DATA = 0x101  # any bytes found after EOI

# Marker codes with no length field / payload (standalone).
_STANDALONE_CODES = {0xD8, 0xD9, 0x01} | set(range(0xD0, 0xD8))  # SOI, EOI, TEM, RSTn

MARKER_NAMES = {
    0xD8: "SOI",
    0xD9: "EOI",
    0x01: "TEM",
    0xDA: "SOS",
    0xDB: "DQT",
    0xC4: "DHT",
    0xDD: "DRI",
    0xFE: "COM",
    SCAN_DATA: "Scan Data",
    TRAILING_DATA: "Trailing Data",
}
for _n in range(0xD0, 0xD8):
    MARKER_NAMES[_n] = f"RST{_n - 0xD0}"
for _n in range(0xE0, 0xF0):
    MARKER_NAMES[_n] = f"APP{_n - 0xE0}"
# SOF0-SOF15, excluding DHT(0xC4), JPG(0xC8), DAC(0xC4 dup/0xCC) which reuse the range for other purposes.
for _n in range(0xC0, 0xD0):
    if _n not in (0xC4, 0xC8, 0xCC):
        MARKER_NAMES[_n] = f"SOF{_n - 0xC0}"

# JPEG restart/frame markers that mark the start of a new scan/frame - used to
# recognize when the entropy-coded data span following an SOS has ended.
_RESTART_RANGE = range(0xD0, 0xD8)


@dataclass
class RawMarker:
    code: int
    offset: int
    length: int | None
    payload: bytes


def marker_name(code: int) -> str:
    return MARKER_NAMES.get(code, f"Unknown (0x{code:02X})")


def walk_markers(data: bytes) -> list[RawMarker]:
    """Walk a JPEG byte stream into an ordered list of marker segments.

    Raises ValueError if `data` doesn't start with the SOI marker (0xFFD8).
    """
    if len(data) < 2 or data[0] != 0xFF or data[1] != 0xD8:
        raise ValueError("Not a valid JPEG file")

    n = len(data)
    markers: list[RawMarker] = [RawMarker(code=0xD8, offset=0, length=None, payload=b"")]
    pos = 2

    while pos < n:
        if data[pos] != 0xFF:
            # Unexpected byte where a marker was expected - stop parsing defensively
            # rather than misinterpreting the rest of the file.
            break

        marker_offset = pos
        while pos < n and data[pos] == 0xFF:
            pos += 1
        if pos >= n:
            break

        code = data[pos]
        pos += 1

        if code == 0x00:
            # Stray stuffed byte outside scan data - not expected, skip defensively.
            continue

        if code == 0xD9:  # EOI
            markers.append(RawMarker(code=code, offset=marker_offset, length=None, payload=b""))
            break

        if code in _STANDALONE_CODES:  # TEM, RSTn appearing outside scan data
            markers.append(RawMarker(code=code, offset=marker_offset, length=None, payload=b""))
            continue

        if pos + 2 > n:
            break  # truncated file, no room for a length field

        length = (data[pos] << 8) | data[pos + 1]
        payload_start = pos + 2
        payload_end = min(payload_start + max(length - 2, 0), n)
        payload = data[payload_start:payload_end]
        markers.append(RawMarker(code=code, offset=marker_offset, length=length, payload=payload))
        pos = payload_end

        if code == 0xDA:  # SOS - scan header consumed, now skip the entropy-coded data
            scan_start = pos
            while pos < n:
                if data[pos] != 0xFF:
                    pos += 1
                    continue
                if pos + 1 >= n:
                    pos += 1
                    break
                nxt = data[pos + 1]
                if nxt == 0x00 or nxt in _RESTART_RANGE or nxt == 0xFF:
                    # 0x00: byte-stuffed 0xFF in entropy data. RSTn: restart marker,
                    # still part of the scan. 0xFF: fill byte, keep scanning.
                    pos += 1 if nxt == 0xFF else 2
                    continue
                break  # a real marker follows - the scan has ended

            markers.append(RawMarker(code=SCAN_DATA, offset=scan_start, length=pos - scan_start, payload=data[scan_start:pos]))

    if pos < n:
        markers.append(RawMarker(code=TRAILING_DATA, offset=pos, length=n - pos, payload=data[pos:]))

    return markers


def serialize_markers(markers: list[RawMarker]) -> bytes:
    """Reassemble a (possibly filtered) marker list back into JPEG bytes.

    Every kept marker's payload/length is emitted exactly as stored, so this
    is a pure concatenation - no re-encoding, no offset recalculation needed,
    as long as in-place edits to a payload never change its length.
    """
    chunks: list[bytes] = []
    for marker in markers:
        if marker.code in (SCAN_DATA, TRAILING_DATA):
            chunks.append(marker.payload)
        elif marker.length is None:
            chunks.append(bytes([0xFF, marker.code]))
        else:
            chunks.append(bytes([0xFF, marker.code]) + marker.length.to_bytes(2, "big") + marker.payload)
    return b"".join(chunks)
