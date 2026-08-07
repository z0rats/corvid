from app.features.username_search.schemas.username_search_schemas import HudsonRockStealerSummary
from app.features.username_search.service.hudson_rock_service import _build_response


def test_build_response_maps_date_computer_and_os_fields():
    data = {
        "stealers": [
            {"date_compromised": "2026-08-01T00:00:00.000Z", "computer_name": "DESKTOP-1", "operating_system": "Windows 10"},
        ],
    }

    result = _build_response("johndoe", data)

    assert result.username == "johndoe"
    assert len(result.stealers) == 1
    assert result.stealers[0].date_compromised == "2026-08-01T00:00:00.000Z"
    assert result.stealers[0].computer_name == "DESKTOP-1"
    assert result.stealers[0].operating_system == "Windows 10"


def test_build_response_handles_multiple_stealers():
    data = {
        "stealers": [
            {"date_compromised": "2026-08-01T00:00:00.000Z", "computer_name": "DESKTOP-1", "operating_system": "Windows 10"},
            {"date_compromised": "2026-07-01T00:00:00.000Z", "computer_name": "DESKTOP-2", "operating_system": "Windows 11"},
        ],
    }

    result = _build_response("johndoe", data)

    assert [s.computer_name for s in result.stealers] == ["DESKTOP-1", "DESKTOP-2"]


def test_build_response_handles_empty_stealers_list():
    result = _build_response("johndoe", {"stealers": []})

    assert result.username == "johndoe"
    assert result.stealers == []


def test_build_response_handles_missing_stealers_key():
    result = _build_response("johndoe", {})

    assert result.stealers == []


def test_build_response_defaults_missing_fields_to_none():
    result = _build_response("johndoe", {"stealers": [{}]})

    assert result.stealers == [HudsonRockStealerSummary(date_compromised=None, computer_name=None, operating_system=None)]
