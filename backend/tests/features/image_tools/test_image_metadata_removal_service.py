import io

import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from app.features.image_tools.service.image_metadata_removal_service import strip_metadata
from app.features.image_tools.utils.jpeg_markers import SCAN_DATA, walk_markers


def _jpeg_with_gps_and_software() -> bytes:
    """A JPEG with both a GPS IFD and a plain (non-GPS) EXIF tag set."""
    image = Image.new("RGB", (50, 50), color="blue")
    exif = image.getexif()
    exif[0x0131] = "TestSoftware 1.0"  # Software tag, lives in IFD0 alongside the GPS pointer
    exif[0x8825] = {
        1: "N",
        2: (IFDRational(40, 1), IFDRational(26, 1), IFDRational(463, 10)),
        3: "W",
        4: (IFDRational(79, 1), IFDRational(56, 1), IFDRational(556, 10)),
        6: IFDRational(100, 1),
    }
    buf = io.BytesIO()
    image.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def _scan_bytes(data: bytes) -> bytes:
    """The entropy-coded scan data span - what must stay byte-identical for a lossless strip."""
    markers = walk_markers(data)
    scan = next(m for m in markers if m.code == SCAN_DATA)
    return scan.payload


class TestStripAllJpeg:
    def test_removes_exif_entirely(self, jpeg_with_software_tag):
        cleaned, media_type, out_filename = strip_metadata(
            "photo.jpg", jpeg_with_software_tag, "all"
        )

        assert media_type == "image/jpeg"
        assert out_filename == "photo_cleaned.jpg"
        reopened = Image.open(io.BytesIO(cleaned))
        assert dict(reopened.getexif()) == {}

    def test_pixel_data_is_byte_identical(self, jpeg_with_software_tag):
        cleaned, _, _ = strip_metadata("photo.jpg", jpeg_with_software_tag, "all")

        assert _scan_bytes(cleaned) == _scan_bytes(jpeg_with_software_tag)

    def test_output_is_smaller_than_input(self, jpeg_with_software_tag):
        cleaned, _, _ = strip_metadata("photo.jpg", jpeg_with_software_tag, "all")

        assert len(cleaned) < len(jpeg_with_software_tag)

    def test_reopened_cleaned_image_is_still_valid(self, jpeg_with_gps):
        cleaned, _, _ = strip_metadata("gps.jpg", jpeg_with_gps, "all")

        reopened = Image.open(io.BytesIO(cleaned))
        reopened.load()
        assert reopened.size == Image.open(io.BytesIO(jpeg_with_gps)).size


class TestStripLocationOnlyJpeg:
    def test_removes_gps_but_keeps_other_exif(self):
        original = _jpeg_with_gps_and_software()

        cleaned, _, _ = strip_metadata("photo.jpg", original, "location_only")

        exif = dict(Image.open(io.BytesIO(cleaned)).getexif())
        assert 0x8825 not in exif
        assert exif.get(0x0131) == "TestSoftware 1.0"

    def test_pixel_data_is_byte_identical(self):
        original = _jpeg_with_gps_and_software()

        cleaned, _, _ = strip_metadata("photo.jpg", original, "location_only")

        assert _scan_bytes(cleaned) == _scan_bytes(original)

    def test_output_same_length_as_input(self):
        """location_only patches bytes in place - file size never changes."""
        original = _jpeg_with_gps_and_software()

        cleaned, _, _ = strip_metadata("photo.jpg", original, "location_only")

        assert len(cleaned) == len(original)

    def test_noop_when_no_gps_present(self, jpeg_with_software_tag):
        cleaned, _, _ = strip_metadata("photo.jpg", jpeg_with_software_tag, "location_only")

        exif = dict(Image.open(io.BytesIO(cleaned)).getexif())
        assert exif.get(0x0131) == "TestSoftware 1.0"


class TestStripNonJpeg:
    def test_removes_metadata_from_png(self, png_bytes):
        cleaned, media_type, out_filename = strip_metadata("photo.png", png_bytes, "all")

        assert media_type == "image/png"
        assert out_filename == "photo_cleaned.png"
        reopened = Image.open(io.BytesIO(cleaned))
        assert reopened.size == (60, 40)

    def test_output_filename_without_extension(self, png_bytes):
        _, _, out_filename = strip_metadata("photo", png_bytes, "all")

        assert out_filename == "photo_cleaned"


class TestStripInvalidInput:
    def test_raises_value_error_for_corrupt_file(self):
        with pytest.raises(ValueError):
            strip_metadata("photo.jpg", b"not an image", "all")
