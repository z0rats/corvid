"""fedresurs_service's pure helpers, tested against JSON shapes captured from real live
requests to fedresurs.ru during development (see the module docstring) - not synthetic
guesses, unlike some of this feature's other Stage-1/2 parser tests."""

from app.features.ru_business_check.service.fedresurs_service import (
    _is_active_bankruptcy,
    _pick_exact_match,
    _profile_url,
)

INN = "7707083893"

# Real shape captured live from https://fedresurs.ru/backend/companies?searchString=<inn>
CLEAN_ROW = {
    "guid": "9348548a-30a3-4344-8cf0-fb1f45c54dfb",
    "ogrn": "1027700132195",
    "inn": INN,
    "name": "ПАО СБЕРБАНК",
    "egrulAddress": "117312, Г.МОСКВА, УЛ. ВАВИЛОВА, Д.19",
    "status": "Действующее",
    "okvedName": "Денежное посредничество прочее",
    "isActive": True,
}

OBSERVATION_ROW = {
    "guid": "e3c2b0f2-219e-448e-9b79-7e55b3efcb39",
    "inn": INN,
    "name": 'ООО "ФУРГОНОФ"',
    "status": (
        "В отношении юридического лица в деле о несостоятельности (банкротстве) введено наблюдение"
    ),
}

RECEIVERSHIP_ROW = {
    "guid": "c3bb33b5-0c41-4ddb-9469-a5fb854c531c",
    "inn": INN,
    "name": 'ООО "КАРТРАНС"',
    "status": (
        "Юридическое лицо признано несостоятельным (банкротом) и в отношении "
        "него открыто конкурсное производство"
    ),
}


class TestPickExactMatch:
    def test_finds_the_row_matching_the_queried_inn(self):
        page_data = [{"inn": "0000000000"}, {"inn": INN, "name": "match"}]
        assert _pick_exact_match(page_data, INN) == {"inn": INN, "name": "match"}

    def test_returns_none_when_no_row_matches(self):
        assert _pick_exact_match([{"inn": "0000000000"}], INN) is None

    def test_returns_none_for_empty_list(self):
        assert _pick_exact_match([], INN) is None

    def test_ignores_near_matches_from_a_fuzzy_searchstring(self):
        # searchString is a fuzzy text search (confirmed live - an overly broad query
        # returned unrelated rows), so a row with a *different* inn must never be picked.
        page_data = [{"inn": "1111111111"}, {"inn": "2222222222"}]
        assert _pick_exact_match(page_data, INN) is None


class TestIsActiveBankruptcy:
    def test_clean_status_is_not_active_bankruptcy(self):
        assert _is_active_bankruptcy(CLEAN_ROW["status"]) is False

    def test_observation_stage_is_active_bankruptcy(self):
        assert _is_active_bankruptcy(OBSERVATION_ROW["status"]) is True

    def test_receivership_stage_is_active_bankruptcy(self):
        assert _is_active_bankruptcy(RECEIVERSHIP_ROW["status"]) is True

    def test_none_status_is_not_active_bankruptcy(self):
        assert _is_active_bankruptcy(None) is False

    def test_empty_status_is_not_active_bankruptcy(self):
        assert _is_active_bankruptcy("") is False

    def test_unrecognized_status_safely_defaults_to_no_flag(self):
        assert _is_active_bankruptcy("Какой-то новый статус, которого нет в списке") is False

    def test_a_terminated_bankruptcy_case_is_not_flagged_even_if_it_mentions_bankruptcy(self):
        assert _is_active_bankruptcy("Производство по делу о банкротстве прекращено") is False


class TestProfileUrl:
    def test_builds_company_url(self):
        assert (
            _profile_url("abc-123", is_individual=False) == "https://fedresurs.ru/company/abc-123"
        )

    def test_builds_person_url(self):
        assert _profile_url("abc-123", is_individual=True) == "https://fedresurs.ru/person/abc-123"

    def test_none_guid_returns_none(self):
        assert _profile_url(None, is_individual=False) is None
