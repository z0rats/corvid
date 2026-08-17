"""pb_nalog_service's pure helpers, tested against JSON shapes captured from real live
requests to pb.nalog.ru during development (see the module docstring) - not synthetic
guesses."""

from app.features.ru_business_check.service.pb_nalog_service import (
    _pick_matching_row,
    parse_detail,
)

INN = "7707083893"

# Real shape captured live from https://pb.nalog.ru/search-proc.json (mode=search-all)
SEARCH_RESULT = {
    "ul": {
        "data": [
            {
                "inn": INN,
                "namep": 'ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО "СБЕРБАНК РОССИИ"',
                "token": "TOK123",
            }
        ],
        "rowCount": 1,
    },
    "ip": {"data": [], "rowCount": 0},
}

# Real shape captured live from https://pb.nalog.ru/company-proc.json (get-response)
DETAIL = {
    "vestnik": [{"code": 5.0, "count": 2.0, "url": "https://www.vestnik-gosreg.ru/x"}],
    "is_p_uchr": False,
    "is_p_ruk": True,
    "masaddress": [
        {
            "massinn": "7710048970",
            "massnamep": 'АКЦИОНЕРНОЕ ОБЩЕСТВО "СБЕРБАНК КИБ"',
            "massnamec": 'АО "СБЕРБАНК КИБ"',
        },
        {
            "massinn": "7736641983",
            "massnamep": 'АКЦИОНЕРНОЕ ОБЩЕСТВО "ДЕЛОВАЯ СРЕДА"',
            "massnamec": 'АО "ДЕЛОВАЯ СРЕДА"',
        },
    ],
    "liquidated": False,
    "is_p": True,
    "type": 1,
    "activeAppeals": [],
}


class TestPickMatchingRow:
    def test_finds_the_row_matching_the_queried_inn_in_the_ul_bucket(self):
        row = _pick_matching_row(SEARCH_RESULT, INN, is_individual=False)
        assert row is not None
        assert row["token"] == "TOK123"

    def test_looks_in_the_ip_bucket_for_individual_entrepreneurs(self):
        search_result = {
            "ul": {"data": [], "rowCount": 0},
            "ip": {"data": [{"inn": "771234567890", "token": "IPTOK"}], "rowCount": 1},
        }
        row = _pick_matching_row(search_result, "771234567890", is_individual=True)
        assert row is not None
        assert row["token"] == "IPTOK"

    def test_returns_none_when_no_row_matches(self):
        assert _pick_matching_row(SEARCH_RESULT, "0000000000", is_individual=False) is None

    def test_returns_none_for_empty_buckets(self):
        empty = {"ul": {"data": [], "rowCount": 0}, "ip": {"data": [], "rowCount": 0}}
        assert _pick_matching_row(empty, INN, is_individual=False) is None

    def test_ignores_near_matches_from_a_fuzzy_query(self):
        # queryAll is a fuzzy text search (confirmed live - a short query returned
        # unrelated rows), so a row with a *different* inn must never be picked.
        search_result = {
            "ul": {"data": [{"inn": "1111111111"}], "rowCount": 1},
            "ip": {"data": [], "rowCount": 0},
        }
        assert _pick_matching_row(search_result, INN, is_individual=False) is None


class TestParseDetail:
    def test_extracts_mass_address_count_and_companies(self):
        result = parse_detail(DETAIL)
        assert result["mass_address_count"] == 2
        assert result["mass_address_companies"] == [
            {"inn": "7710048970", "name": 'АКЦИОНЕРНОЕ ОБЩЕСТВО "СБЕРБАНК КИБ"'},
            {"inn": "7736641983", "name": 'АКЦИОНЕРНОЕ ОБЩЕСТВО "ДЕЛОВАЯ СРЕДА"'},
        ]

    def test_zero_mass_address_when_absent(self):
        result = parse_detail({})
        assert result["mass_address_count"] == 0
        assert result["mass_address_companies"] == []

    def test_marks_checked_and_found(self):
        result = parse_detail(DETAIL)
        assert result["checked"] is True
        assert result["found"] is True

    def test_caps_displayed_companies_at_the_display_limit(self):
        big_masaddress = [{"massinn": str(i), "massnamep": f"ООО {i}"} for i in range(25)]
        result = parse_detail({"masaddress": big_masaddress})
        assert result["mass_address_count"] == 25
        assert len(result["mass_address_companies"]) == 10

    def test_falls_back_to_massnamec_when_massnamep_missing(self):
        result = parse_detail({"masaddress": [{"massinn": "1", "massnamec": "ООО Компакт"}]})
        assert result["mass_address_companies"] == [{"inn": "1", "name": "ООО Компакт"}]
