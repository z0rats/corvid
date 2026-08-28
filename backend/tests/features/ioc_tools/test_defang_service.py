import pytest

from app.features.ioc_tools.ioc_defanger.service.defang_service import (
    batch_process_iocs,
    defang_single_ioc,
    extract_ioc_types_from_data,
    fang_single_ioc,
    process_iocs_with_type_detection,
    process_iocs_without_type_detection,
)
from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import extract_iocs


class TestDefangSingleIoc:
    def test_defangs_an_ip(self):
        assert defang_single_ioc("1.2.3.4") == "1[.]2[.]3[.]4"

    def test_non_string_input_is_returned_unchanged(self):
        assert defang_single_ioc(None) is None
        assert defang_single_ioc("") == ""


class TestFangSingleIoc:
    def test_fangs_a_defanged_ip(self):
        assert fang_single_ioc("1[.]2[.]3[.]4") == "1.2.3.4"

    def test_non_string_input_is_returned_unchanged(self):
        assert fang_single_ioc(None) is None
        assert fang_single_ioc("") == ""


class TestExtractIocTypesFromData:
    def test_maps_each_ioc_value_to_its_detected_type(self):
        extracted = extract_iocs("1.2.3.4 evil.com user@evil.com")
        type_map = extract_ioc_types_from_data(extracted)

        assert type_map["1.2.3.4"] == ["IP Address"]
        assert type_map["evil.com"] == ["Domain"]
        assert type_map["user@evil.com"] == ["Email"]

    def test_a_repeated_ioc_does_not_get_duplicate_type_entries(self):
        extracted = extract_iocs("1.2.3.4 1.2.3.4")
        type_map = extract_ioc_types_from_data(extracted)

        assert type_map["1.2.3.4"] == ["IP Address"]

    def test_empty_extraction_returns_an_empty_map(self):
        extracted = extract_iocs("just some plain text with no indicators")
        assert extract_ioc_types_from_data(extracted) == {}


class TestProcessIocsWithTypeDetection:
    def test_defangs_each_ioc_and_attaches_detected_types(self):
        results = process_iocs_with_type_detection("1.2.3.4\nevil.com", "defang")

        by_original = {r.original: r for r in results}
        assert by_original["1.2.3.4"].processed == "1[.]2[.]3[.]4"
        assert by_original["1.2.3.4"].types == ["IP Address"]
        assert by_original["1.2.3.4"].changed is True
        assert by_original["evil.com"].types == ["Domain"]

    def test_fangs_each_ioc_when_operation_is_fang(self):
        results = process_iocs_with_type_detection("1[.]2[.]3[.]4", "fang")

        assert results[0].original == "1[.]2[.]3[.]4"
        assert results[0].processed == "1.2.3.4"
        assert results[0].changed is True

    def test_no_ioc_like_content_returns_an_empty_list(self):
        assert process_iocs_with_type_detection("just plain words", "defang") == []

    def test_whitespace_only_text_returns_an_empty_list(self):
        assert process_iocs_with_type_detection("   ", "defang") == []

    def test_falls_back_to_untyped_processing_when_extraction_raises(self, monkeypatch):
        import app.features.ioc_tools.ioc_defanger.service.defang_service as defang_service_module

        def _boom(_text):
            raise RuntimeError("extractor blew up")

        monkeypatch.setattr(defang_service_module, "extract_iocs", _boom)

        results = process_iocs_with_type_detection("1.2.3.4", "defang")

        assert len(results) == 1
        assert results[0].original == "1.2.3.4"
        assert results[0].processed == "1[.]2[.]3[.]4"
        assert results[0].types == ["Unknown"]


class TestProcessIocsWithoutTypeDetection:
    def test_processes_each_ioc_with_unknown_type(self):
        results = process_iocs_without_type_detection(["1.2.3.4", "evil.com"], defang_single_ioc)

        assert [r.original for r in results] == ["1.2.3.4", "evil.com"]
        assert all(r.types == ["Unknown"] for r in results)
        assert results[0].processed == "1[.]2[.]3[.]4"

    def test_empty_input_returns_an_empty_list(self):
        assert process_iocs_without_type_detection([], defang_single_ioc) == []


class TestBatchProcessIocs:
    def test_defangs_and_returns_stats(self):
        response = batch_process_iocs("1.2.3.4\nevil.com", "defang")

        assert response.total_processed == 2
        assert response.total_changed == 2
        assert {r.processed for r in response.results} == {"1[.]2[.]3[.]4", "evil[.]com"}

    def test_fangs_when_operation_is_fang(self):
        response = batch_process_iocs("1[.]2[.]3[.]4", "fang")

        assert response.total_processed == 1
        assert response.results[0].processed == "1.2.3.4"

    def test_defaults_to_defang_when_operation_is_omitted(self):
        response = batch_process_iocs("1.2.3.4")
        assert response.results[0].processed == "1[.]2[.]3[.]4"

    def test_invalid_operation_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid operation"):
            batch_process_iocs("1.2.3.4", "delete")

    def test_no_ioc_like_content_returns_zero_stats(self):
        response = batch_process_iocs("just plain words", "defang")

        assert response.results == []
        assert response.total_processed == 0
        assert response.total_changed == 0
