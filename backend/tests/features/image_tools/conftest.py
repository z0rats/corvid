import io

import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational


def _jpeg_bytes(exif=None) -> bytes:
    image = Image.new('RGB', (100, 80), color='red')
    buf = io.BytesIO()
    if exif is not None:
        image.save(buf, format='JPEG', exif=exif)
    else:
        image.save(buf, format='JPEG')
    return buf.getvalue()


@pytest.fixture
def plain_jpeg_bytes() -> bytes:
    """A minimal JPEG with no EXIF data at all."""
    return _jpeg_bytes()


@pytest.fixture
def jpeg_with_software_tag() -> bytes:
    """A JPEG carrying a single basic EXIF tag (Software)."""
    image = Image.new('RGB', (100, 80), color='red')
    exif = image.getexif()
    exif[0x0131] = 'TestSoftware 1.0'  # Software tag
    return _jpeg_bytes(exif=exif)


@pytest.fixture
def jpeg_with_gps() -> bytes:
    """A JPEG with EXIF GPS coordinates: 40 26 46.3 N, 79 56 55.6 W, altitude 100m."""
    image = Image.new('RGB', (50, 50), color='blue')
    exif = image.getexif()
    gps_ifd = {
        1: 'N',
        2: (IFDRational(40, 1), IFDRational(26, 1), IFDRational(463, 10)),
        3: 'W',
        4: (IFDRational(79, 1), IFDRational(56, 1), IFDRational(556, 10)),
        6: IFDRational(100, 1),
    }
    exif[0x8825] = gps_ifd
    return _jpeg_bytes(exif=exif)


@pytest.fixture
def png_bytes() -> bytes:
    """A plain PNG, which typically carries no EXIF data."""
    image = Image.new('RGB', (60, 40), color='green')
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()
