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


def _row(name):
    # The live search-result row's contract fields (`t` token, `i` ИНН, `o` ОГРН, `n` name).
    return {"t": "row-token", "i": "7712345678", "o": "1234567890123", "n": name}


class TestSelectRow:
    def test_no_rows_raises_a_clean_not_found_error(self):
        with pytest.raises(EgrulError, match="Ничего не найдено"):
            _select_row({"rows": []})

    def test_a_missing_rows_list_is_schema_drift_not_not_found(self):
        with pytest.raises(EgrulError, match="схема ответа изменилась"):
            _select_row({})

    def test_a_row_missing_a_contract_field_is_schema_drift(self):
        with pytest.raises(EgrulError, match="нет поля «i»"):
            _select_row({"rows": [{"t": "row-token", "n": "ООО Ромашка", "o": "1"}]})

    def test_single_row_is_returned_directly(self):
        row = _row("ООО Ромашка")
        assert _select_row({"rows": [row]}) is row

    def test_multiple_rows_raise_ambiguous_match_with_one_candidate_per_row(self):
        rows = [_row("ООО Ромашка №1"), _row("ООО Ромашка №2")]
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


def test_a_poll_answer_that_is_not_an_object_is_schema_drift(patch_httpx_transport):
    import asyncio

    import httpx

    from app.features.ru_business_check.service.egrul_service import _poll_json

    patch_httpx_transport(lambda request: httpx.Response(200, json=["not", "an", "object"]))

    async def go():
        async with httpx.AsyncClient() as client:
            await _poll_json(
                client, "https://egrul.nalog.ru/x", interval=0, max_attempts=1, ready=bool
            )

    with pytest.raises(EgrulError, match="схема ответа изменилась"):
        asyncio.run(go())
