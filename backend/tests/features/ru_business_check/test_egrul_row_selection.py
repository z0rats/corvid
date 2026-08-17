"""egrul_service's search-row selection/candidate-mapping logic - pure functions, no
network involved. Field-name fallbacks in `_row_to_candidate` are best-effort (unverified
against a live capture, see the module docstring), so these fixtures exercise a few
plausible key-name variants rather than committing to one true shape."""

import pytest

from app.features.ru_business_check.service.egrul_service import (
    EgrulAmbiguousMatch,
    EgrulError,
    _row_to_candidate,
    _select_row,
)


class TestSelectRow:
    def test_no_rows_raises_a_clean_not_found_error(self):
        with pytest.raises(EgrulError, match="Ничего не найдено"):
            _select_row({"rows": []})
        with pytest.raises(EgrulError, match="Ничего не найдено"):
            _select_row({})

    def test_single_row_is_returned_directly(self):
        row = {"t": "row-token", "n": "ООО Ромашка"}
        assert _select_row({"rows": [row]}) is row

    def test_multiple_rows_raise_ambiguous_match_with_one_candidate_per_row(self):
        rows = [{"n": "ООО Ромашка №1"}, {"n": "ООО Ромашка №2"}]
        with pytest.raises(EgrulAmbiguousMatch) as exc_info:
            _select_row({"rows": rows})

        assert len(exc_info.value.candidates) == 2
        assert "2 совпадени" in str(exc_info.value)


class TestRowToCandidate:
    def test_maps_a_plausible_field_set(self):
        row = {
            "n": "ООО Ромашка",
            "i": "7712345678",
            "o": "1234567890123",
            "a": "г. Москва",
            "s": "Действующее",
        }
        candidate = _row_to_candidate(row)

        assert candidate == {
            "name": "ООО Ромашка",
            "inn": "7712345678",
            "ogrn": "1234567890123",
            "address": "г. Москва",
            "status": "Действующее",
        }

    def test_falls_back_across_alternate_key_names(self):
        row = {
            "name": "ООО Ромашка",
            "inn": "7712345678",
            "ogrn": "1234567890123",
            "address": "г. Москва",
            "status": "Действующее",
        }
        candidate = _row_to_candidate(row)

        assert candidate["name"] == "ООО Ромашка"
        assert candidate["inn"] == "7712345678"

    def test_missing_fields_are_none_not_raising(self):
        candidate = _row_to_candidate({})

        assert candidate == {
            "name": None,
            "inn": None,
            "ogrn": None,
            "address": None,
            "status": None,
        }
