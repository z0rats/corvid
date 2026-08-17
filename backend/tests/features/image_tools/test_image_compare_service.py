import pytest

from app.features.image_tools.service.image_compare_service import compare_images


def _diffs_by_field(response):
    return {d.field: d for d in response.field_diffs}


class TestFieldDiffs:
    def test_identical_files_have_no_differing_fields(self, jpeg_with_software_tag):
        result = compare_images("a.jpg", jpeg_with_software_tag, "b.jpg", jpeg_with_software_tag)

        assert result.summary.differ_count == 0
        assert result.summary.only_left_count == 0
        assert result.summary.only_right_count == 0
        assert result.summary.match_count > 0

    def test_field_only_on_one_side_is_flagged(self, jpeg_with_software_tag, plain_jpeg_bytes):
        result = compare_images("a.jpg", jpeg_with_software_tag, "b.jpg", plain_jpeg_bytes)

        diffs = _diffs_by_field(result)
        assert diffs["Image Software"].status == "only_left"
        assert diffs["Image Software"].left_value == "TestSoftware 1.0"
        assert diffs["Image Software"].right_value is None

    def test_rejects_invalid_left_image(self, plain_jpeg_bytes):
        with pytest.raises(ValueError):
            compare_images("a.jpg", b"not an image", "b.jpg", plain_jpeg_bytes)

    def test_rejects_invalid_right_image(self, plain_jpeg_bytes):
        with pytest.raises(ValueError):
            compare_images("a.jpg", plain_jpeg_bytes, "b.jpg", b"not an image")


class TestPerceptualHashDistance:
    def test_identical_pixels_yield_zero_distance_and_likely_match(self, plain_jpeg_bytes):
        result = compare_images("a.jpg", plain_jpeg_bytes, "b.jpg", plain_jpeg_bytes)

        assert result.phash_distance == 0
        assert result.pixels_likely_match is True

    def test_very_different_images_are_not_a_pixel_match(self, plain_jpeg_bytes, png_bytes):
        result = compare_images("a.jpg", plain_jpeg_bytes, "b.png", png_bytes)

        assert result.phash_distance > 10
        assert result.pixels_likely_match is False
