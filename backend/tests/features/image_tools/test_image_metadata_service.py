import hashlib

import pytest

from app.features.image_tools.service.image_metadata_service import analyze_image_content


class TestFileInfo:
    def test_extracts_basic_properties(self, plain_jpeg_bytes):
        result = analyze_image_content('photo.jpg', plain_jpeg_bytes)

        assert result.file_info.filename == 'photo.jpg'
        assert result.file_info.format == 'JPEG'
        assert result.file_info.mime_type == 'image/jpeg'
        assert result.file_info.width == 100
        assert result.file_info.height == 80
        assert result.file_info.mode == 'RGB'
        assert result.file_info.file_size == len(plain_jpeg_bytes)

    def test_png_is_analyzed_without_error(self, png_bytes):
        result = analyze_image_content('shot.png', png_bytes)

        assert result.file_info.format == 'PNG'
        assert result.file_info.width == 60
        assert result.file_info.height == 40

    def test_invalid_image_data_raises_value_error(self):
        with pytest.raises(ValueError):
            analyze_image_content('not_an_image.jpg', b'this is not image data')


class TestHashes:
    def test_hashes_match_hashlib(self, plain_jpeg_bytes):
        result = analyze_image_content('photo.jpg', plain_jpeg_bytes)

        assert result.hashes.md5 == hashlib.md5(plain_jpeg_bytes).hexdigest()
        assert result.hashes.sha1 == hashlib.sha1(plain_jpeg_bytes).hexdigest()
        assert result.hashes.sha256 == hashlib.sha256(plain_jpeg_bytes).hexdigest()


class TestExifExtraction:
    def test_no_exif_returns_empty_dict(self, plain_jpeg_bytes):
        result = analyze_image_content('photo.jpg', plain_jpeg_bytes)

        assert result.exif == {}
        assert result.gps is None
        assert result.has_thumbnail is False
        assert result.thumbnail_base64 is None

    def test_software_tag_is_extracted(self, jpeg_with_software_tag):
        result = analyze_image_content('photo.jpg', jpeg_with_software_tag)

        assert result.exif.get('Image Software') == 'TestSoftware 1.0'

    def test_thumbnail_binary_tags_are_excluded_from_exif_dict(self, jpeg_with_gps):
        result = analyze_image_content('photo.jpg', jpeg_with_gps)

        assert 'JPEGThumbnail' not in result.exif
        assert 'TIFFThumbnail' not in result.exif


class TestGpsExtraction:
    def test_dms_coordinates_converted_to_decimal(self, jpeg_with_gps):
        result = analyze_image_content('photo.jpg', jpeg_with_gps)

        assert result.gps is not None
        # 40 26 46.3 N -> 40.446194..., 79 56 55.6 W -> -79.948778... (negative for West)
        assert result.gps.latitude == pytest.approx(40.446194, abs=1e-5)
        assert result.gps.longitude == pytest.approx(-79.948778, abs=1e-5)
        assert result.gps.altitude == pytest.approx(100.0)

    def test_map_url_contains_coordinates(self, jpeg_with_gps):
        result = analyze_image_content('photo.jpg', jpeg_with_gps)

        assert str(result.gps.latitude) in result.gps.map_url
        assert str(result.gps.longitude) in result.gps.map_url

    def test_no_gps_tags_yields_none(self, jpeg_with_software_tag):
        result = analyze_image_content('photo.jpg', jpeg_with_software_tag)

        assert result.gps is None
