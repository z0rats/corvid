import pytest

from app.features.image_tools.service.image_structure_service import analyze_jpeg_structure


class TestMarkerMap:
    def test_starts_with_soi_and_ends_with_eoi(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        assert result.markers[0].marker_type == 'SOI'
        assert result.markers[0].offset == 0
        assert result.markers[-1].marker_type == 'EOI'

    def test_includes_dqt_and_dht_and_sof_markers(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        marker_types = [m.marker_type for m in result.markers]
        assert 'DQT' in marker_types
        assert 'DHT' in marker_types
        assert any(t.startswith('SOF') for t in marker_types)
        assert 'SOS' in marker_types

    def test_scan_data_and_non_scan_segments_have_expected_hex_preview(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        scan_segments = [m for m in result.markers if m.marker_type == 'Scan Data']
        assert len(scan_segments) == 1
        assert scan_segments[0].raw_hex is None

        dqt_segments = [m for m in result.markers if m.marker_type == 'DQT']
        assert dqt_segments[0].raw_hex is not None

    def test_rejects_non_jpeg_input(self, png_bytes):
        with pytest.raises(ValueError):
            analyze_jpeg_structure('photo.png', png_bytes)


class TestQuantizationTables:
    def test_returns_full_8x8_tables(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        assert len(result.quantization_tables) >= 1
        for table in result.quantization_tables:
            assert len(table.values) == 64
            assert table.precision in (8, 16)

    def test_quality_estimate_close_to_requested_quality(self, jpeg_quality_80_bytes):
        result = analyze_jpeg_structure('photo.jpg', jpeg_quality_80_bytes)

        assert result.overall_quality_estimate is not None
        assert abs(result.overall_quality_estimate - 80) <= 5


class TestHuffmanTables:
    def test_returns_code_length_distributions(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        assert len(result.huffman_tables) >= 1
        for table in result.huffman_tables:
            assert table.table_class in ('DC', 'AC')
            assert len(table.code_lengths) == 16
            assert table.total_codes == sum(table.code_lengths)


class TestFrameInfo:
    def test_baseline_frame_parameters(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        assert result.frame is not None
        assert result.frame.is_progressive is False
        assert result.frame.width == 100
        assert result.frame.height == 80
        assert len(result.frame.components) == 3

    def test_progressive_frame_is_detected(self, progressive_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', progressive_jpeg_bytes)

        assert result.frame.is_progressive is True
        assert 'Progressive' in result.frame.frame_type


class TestDerivedMetrics:
    def test_compression_ratio_and_bits_per_pixel_are_positive(self, plain_jpeg_bytes):
        result = analyze_jpeg_structure('photo.jpg', plain_jpeg_bytes)

        assert result.compression_ratio > 0
        assert result.bits_per_pixel > 0
        assert result.file_size == len(plain_jpeg_bytes)
