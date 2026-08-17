import io

import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from app.features.image_tools.service.image_anomaly_service import analyze_image_anomalies


def _checks_by_name(response):
    return {finding.check: finding for finding in response.findings}


class TestNoAnomalies:
    def test_plain_jpeg_has_no_findings(self, plain_jpeg_bytes):
        result = analyze_image_anomalies("photo.jpg", plain_jpeg_bytes)

        assert result.findings == []
        assert result.checks_run > 0

    def test_rejects_corrupt_file(self):
        with pytest.raises(ValueError):
            analyze_image_anomalies("photo.jpg", b"not an image")


class TestEditingSoftwareCheck:
    def test_flags_known_editor_signature(self):
        image = Image.new("RGB", (60, 40), color="red")
        exif = image.getexif()
        exif[0x0131] = "Adobe Photoshop 25.0"
        buf = io.BytesIO()
        image.save(buf, format="JPEG", exif=exif)

        result = analyze_image_anomalies("photo.jpg", buf.getvalue())

        findings = _checks_by_name(result)
        assert "editing_software" in findings
        assert "Photoshop" in findings["editing_software"].message

    def test_does_not_flag_camera_software(self, jpeg_with_software_tag):
        result = analyze_image_anomalies("photo.jpg", jpeg_with_software_tag)

        assert "editing_software" not in _checks_by_name(result)


class TestTimestampConsistencyCheck:
    def test_flags_diverging_timestamps(self):
        image = Image.new("RGB", (60, 40), color="red")
        exif = image.getexif()
        exif[0x0132] = "2020:01:01 12:00:00"  # DateTime (IFD0)
        ifd = exif.get_ifd(0x8769)
        ifd[0x9003] = "2024:06:15 08:30:00"  # DateTimeOriginal
        buf = io.BytesIO()
        image.save(buf, format="JPEG", exif=exif)

        result = analyze_image_anomalies("photo.jpg", buf.getvalue())

        assert "timestamp_consistency" in _checks_by_name(result)

    def test_no_finding_with_a_single_timestamp(self, jpeg_with_software_tag):
        result = analyze_image_anomalies("photo.jpg", jpeg_with_software_tag)

        assert "timestamp_consistency" not in _checks_by_name(result)


class TestGpsTimestampCheck:
    def test_flags_gps_time_far_from_capture_time(self):
        image = Image.new("RGB", (60, 40), color="red")
        exif = image.getexif()
        exif.get_ifd(0x8769)[0x9003] = "2024:06:15 08:30:00"  # DateTimeOriginal
        exif[0x8825] = {
            7: (IFDRational(10, 1), IFDRational(0, 1), IFDRational(0, 1)),  # GPSTimeStamp
            29: "2024:01:01",  # GPSDateStamp - over 5 months earlier
        }
        buf = io.BytesIO()
        image.save(buf, format="JPEG", exif=exif)

        result = analyze_image_anomalies("photo.jpg", buf.getvalue())

        assert "gps_timestamp_mismatch" in _checks_by_name(result)

    def test_no_finding_when_gps_time_matches_capture_time(self):
        image = Image.new("RGB", (60, 40), color="red")
        exif = image.getexif()
        exif.get_ifd(0x8769)[0x9003] = "2024:06:15 08:30:00"
        exif[0x8825] = {
            7: (IFDRational(8, 1), IFDRational(35, 1), IFDRational(0, 1)),
            29: "2024:06:15",
        }
        buf = io.BytesIO()
        image.save(buf, format="JPEG", exif=exif)

        result = analyze_image_anomalies("photo.jpg", buf.getvalue())

        assert "gps_timestamp_mismatch" not in _checks_by_name(result)

    def test_no_finding_when_gps_timestamp_absent(self, jpeg_with_software_tag):
        result = analyze_image_anomalies("photo.jpg", jpeg_with_software_tag)

        assert "gps_timestamp_mismatch" not in _checks_by_name(result)


class TestTrailingDataCheck:
    def test_flags_bytes_appended_after_eoi(self, plain_jpeg_bytes):
        tampered = plain_jpeg_bytes + b"hidden payload after EOI"

        result = analyze_image_anomalies("photo.jpg", tampered)

        findings = _checks_by_name(result)
        assert "trailing_data" in findings
        assert "24" in findings["trailing_data"].message  # len(b'hidden payload after EOI')

    def test_no_finding_without_trailing_data(self, plain_jpeg_bytes):
        result = analyze_image_anomalies("photo.jpg", plain_jpeg_bytes)

        assert "trailing_data" not in _checks_by_name(result)


class TestNonJpegFormats:
    def test_png_skips_jpeg_only_checks_without_error(self, png_bytes):
        result = analyze_image_anomalies("photo.png", png_bytes)

        assert "trailing_data" not in _checks_by_name(result)
        assert "marker_order" not in _checks_by_name(result)
        assert "quantization_tables" not in _checks_by_name(result)
