import io

import pytest
from PIL import Image

from app.features.image_tools.service.image_visual_analysis_service import analyze_image_visuals


def _solid_jpeg_bytes(color) -> bytes:
    image = Image.new('RGB', (64, 64), color=color)
    buf = io.BytesIO()
    image.save(buf, format='JPEG')
    return buf.getvalue()


class TestHistograms:
    def test_returns_256_bin_histograms_for_every_channel(self, plain_jpeg_bytes):
        result = analyze_image_visuals('photo.jpg', plain_jpeg_bytes)

        for channel in (result.histograms.red, result.histograms.green, result.histograms.blue,
                        result.histograms.luminance, result.histograms.cb, result.histograms.cr):
            assert len(channel) == 256
            assert sum(channel) > 0

    def test_pure_red_image_peaks_in_the_red_channel_high_bins(self):
        data = _solid_jpeg_bytes((255, 0, 0))

        result = analyze_image_visuals('red.jpg', data)

        red_peak_bin = max(range(256), key=lambda i: result.histograms.red[i])
        green_peak_bin = max(range(256), key=lambda i: result.histograms.green[i])
        assert red_peak_bin > 200
        assert green_peak_bin < 50

    def test_rejects_corrupt_file(self):
        with pytest.raises(ValueError):
            analyze_image_visuals('photo.jpg', b'not an image')


class TestVectorscope:
    def test_returns_a_bin_count_squared_grid(self, plain_jpeg_bytes):
        result = analyze_image_visuals('photo.jpg', plain_jpeg_bytes)

        assert len(result.vectorscope.counts) == result.vectorscope.bin_count ** 2
        assert result.vectorscope.max_count == max(result.vectorscope.counts)

    def test_solid_color_image_concentrates_into_a_single_bin(self):
        data = _solid_jpeg_bytes((10, 200, 50))

        result = analyze_image_visuals('solid.jpg', data)

        non_empty_bins = sum(1 for c in result.vectorscope.counts if c > 0)
        assert non_empty_bins <= 4  # allow a little JPEG quantization noise at block edges


class TestDownsampling:
    def test_large_image_is_analyzed_without_error(self):
        image = Image.new('RGB', (1200, 900), color=(20, 150, 220))
        buf = io.BytesIO()
        image.save(buf, format='JPEG')

        result = analyze_image_visuals('big.jpg', buf.getvalue())

        assert sum(result.histograms.luminance) > 0
