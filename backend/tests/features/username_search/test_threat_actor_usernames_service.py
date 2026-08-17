from app.features.username_search.service.threat_actor_usernames_service import _extract_found_sites


def test_extract_found_sites_maps_forum_and_username_fields():
    results = [
        {"username": "Admin", "forum": "Cracked", "logo": "/static/logos/cracked_usernames.png"}
    ]

    found_sites = _extract_found_sites(results)

    assert found_sites == [
        {
            "site_name": "Cracked",
            "url_user": "",
            "http_status": None,
            "extra": {"username": "Admin", "logo": "/static/logos/cracked_usernames.png"},
        }
    ]


def test_extract_found_sites_handles_multiple_results():
    results = [
        {"username": "admin", "forum": "Xss", "logo": "/static/logos/xss_usernames.png"},
        {"username": "Admin", "forum": "Spear", "logo": "/static/logos/spear_usernames.png"},
    ]

    found_sites = _extract_found_sites(results)

    assert [site["site_name"] for site in found_sites] == ["Xss", "Spear"]


def test_extract_found_sites_handles_empty_results():
    assert _extract_found_sites([]) == []


def test_extract_found_sites_defaults_missing_fields():
    found_sites = _extract_found_sites([{}])

    assert found_sites == [
        {
            "site_name": "",
            "url_user": "",
            "http_status": None,
            "extra": {"username": None, "logo": None},
        }
    ]
