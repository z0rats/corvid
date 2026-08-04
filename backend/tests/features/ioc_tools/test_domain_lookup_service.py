from app.features.ioc_tools.domain_finder.service.domain_lookup_service import (
    deduplicate_scan_results,
)


def _result(url, uuid):
    return {"task": {"uuid": uuid}, "page": {"url": url}, "expanded": False}


def test_deduplicate_scan_results_keeps_first_occurrence_per_url():
    # urlscan.io returns newest-first, so the first occurrence of a URL is the latest scan
    results = [
        _result("https://example.com/", "newest-uuid"),
        _result("https://example.com/", "older-uuid"),
        _result("https://sub.example.com/", "other-uuid"),
    ]

    deduped = deduplicate_scan_results(results)

    assert [r["task"]["uuid"] for r in deduped] == ["newest-uuid", "other-uuid"]


def test_deduplicate_scan_results_keeps_entries_missing_page_url():
    results = [
        {"task": {"uuid": "no-page"}, "page": None, "expanded": False},
        {"task": {"uuid": "no-url"}, "page": {}, "expanded": False},
    ]

    deduped = deduplicate_scan_results(results)

    assert len(deduped) == 2


def test_deduplicate_scan_results_handles_empty_list():
    assert deduplicate_scan_results([]) == []
