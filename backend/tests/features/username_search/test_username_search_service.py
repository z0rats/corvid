from types import SimpleNamespace

from app.features.username_search.service.username_search_service import _extract_found_sites


def _status(found=True, ids_data=None):
    return SimpleNamespace(is_found=lambda: found, ids_data=ids_data)


def test_extracts_discovered_usernames_links_and_names():
    results = {
        "GitHub": {
            "status": _status(ids_data={"fullname": " John Smith "}),
            "url_user": "https://github.com/jsmith",
            "http_status": 200,
            "ids_usernames": {"jsmith": "username", "JSmith_alt": "username", "12345": "vk_id"},
            "ids_links": ["https://jsmith.dev"],
        }
    }

    (site,) = _extract_found_sites(results, "jsmith")

    assert site["extra"] == {
        "discovered_usernames": [
            {"value": "JSmith_alt", "type": "username"},
            {"value": "12345", "type": "vk_id"},
        ],
        "discovered_links": ["https://jsmith.dev"],
        "discovered_names": ["John Smith"],
    }


def test_extra_is_none_when_nothing_discovered_and_unfound_sites_skipped():
    results = {
        "Plain": {"status": _status(), "url_user": "https://x.test/u", "http_status": 200},
        "Missing": {"status": _status(found=False), "url_user": "https://y.test/u"},
    }

    sites = _extract_found_sites(results, "u")

    assert [s["site_name"] for s in sites] == ["Plain"]
    assert sites[0]["extra"] is None
