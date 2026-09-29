"""fedresurs_service's publications parsing/role logic, against JSON shapes captured live from
fedresurs.ru/backend/companies/<guid>/publications on 2026-09-28 (ПАО СБЕРБАНК, whose
publications are dominated by "намерение кредитора" messages about *other* companies - the
exact case the role rule exists for)."""

import asyncio
import datetime

import httpx
import pytest

from app.features.ru_business_check.service.fedresurs_service import (
    FedresursBlocked,
    FedresursError,
    classify_status,
    fetch_fedresurs_status,
    is_fully_checked,
    parse_publications,
)

BANK = "9348548a-30a3-4344-8cf0-fb1f45c54dfb"
DEBTOR = "a7034eee-4936-49a1-848a-cca587ca9e5c"
OTHER = "241c7095-281b-4f88-b54a-1939c244c150"
TODAY = datetime.date(2026, 9, 28)

CREDITOR_INTENT = "Намерение кредитора обратиться в суд с заявлением о банкротстве"
DEBTOR_INTENT = "Намерение должника обратиться в суд с заявлением о банкротстве"


def _run(coro):
    return asyncio.run(coro)


def _message(
    type_=CREDITOR_INTENT,
    *,
    publisher=BANK,
    participants=(BANK, DEBTOR),
    date="2026-09-20T10:00:00.1",
    annulled=False,
    publication_type="SfactMessage",
    guid="m-1",
):
    return {
        "publicationType": publication_type,
        "guid": guid,
        "number": "100",
        "datePublish": date,
        "isAnnulled": annulled,
        "type": type_,
        "publisher": {"name": "P", "guid": publisher, "type": "Company"} if publisher else None,
        "participants": [{"name": "X", "guid": g, "type": "Company"} for g in participants],
    }


def _page(*messages, found=None):
    return {"pageData": list(messages), "found": len(messages) if found is None else found}


class TestRoleRules:
    def test_bank_publishing_intents_about_others_raises_no_signal_for_the_bank(self):
        # The bank is publisher AND participant of its own creditor-intent messages.
        parsed = parse_publications(_page(_message()), BANK, today=TODAY)
        assert parsed["signals"] == []
        assert parsed["messages"][0]["role"] == "publisher"

    def test_debtor_named_in_a_creditors_intent_gets_the_signal(self):
        parsed = parse_publications(_page(_message()), DEBTOR, today=TODAY)
        assert [s["code"] for s in parsed["signals"]] == ["creditor_bankruptcy_intent"]

    def test_creditor_intent_with_publisher_lacking_a_guid_is_not_a_signal_but_is_noted(self):
        message = _message()
        message["publisher"] = {"name": "?", "type": "Company"}
        parsed = parse_publications(_page(message), DEBTOR, today=TODAY)
        assert parsed["signals"] == []
        assert "не удалось определить роль" in parsed["note"]

    def test_creditor_intent_with_a_null_publisher_is_noted_as_unclear(self):
        message = _message(publisher=None, participants=(DEBTOR,))
        parsed = parse_publications(_page(message), DEBTOR, today=TODAY)
        assert parsed["signals"] == []
        assert len(parsed["messages"]) == 1
        assert "не удалось определить роль" in parsed["note"]

    def test_debtors_own_intent_needs_the_company_as_publisher(self):
        own = _message(DEBTOR_INTENT, publisher=DEBTOR, participants=(DEBTOR,))
        about_other = _message(DEBTOR_INTENT, publisher=OTHER, participants=(OTHER, DEBTOR))
        assert [
            s["code"] for s in parse_publications(_page(own), DEBTOR, today=TODAY)["signals"]
        ] == ["debtor_bankruptcy_intent"]
        assert parse_publications(_page(about_other), DEBTOR, today=TODAY)["signals"] == []

    def test_debtor_intent_naming_the_company_with_an_unknown_publisher_is_unclear(self):
        message = _message(DEBTOR_INTENT, publisher=None, participants=(DEBTOR,))
        parsed = parse_publications(_page(message), DEBTOR, today=TODAY)
        assert parsed["signals"] == []
        assert "не удалось определить роль" in parsed["note"]

    def test_unreliable_information_is_published_by_egrul_without_a_guid(self):
        message = _message("Недостоверность сведений", publisher=None, participants=(DEBTOR,))
        parsed = parse_publications(_page(message), DEBTOR, today=TODAY)
        assert [s["code"] for s in parsed["signals"]] == ["unreliable_information"]

    def test_company_absent_from_publisher_and_participants_is_unclear_not_clean(self):
        parsed = parse_publications(_page(_message()), "someone-else", today=TODAY)
        assert parsed["signals"] == []
        assert parsed["messages"][0]["role"] is None
        assert "не удалось определить роль" in parsed["note"]


class TestFilteringAndWindow:
    def test_annulled_and_non_sfact_messages_are_ignored(self):
        parsed = parse_publications(
            _page(
                _message(annulled=True, guid="a"),
                _message(publication_type="BankruptcyMessage", guid="b"),
            ),
            DEBTOR,
            today=TODAY,
        )
        assert parsed["messages"] == []
        assert parsed["signals"] == []

    def test_reorganization_counts_only_inside_the_window(self):
        fresh = _message("Реорганизация юридического лица", date="2026-03-01T00:00:00", guid="f")
        stale = _message("Реорганизация юридического лица", date="2022-03-01T00:00:00", guid="s")
        parsed = parse_publications(_page(fresh, stale), DEBTOR, today=TODAY)
        assert [s["date"] for s in parsed["signals"]] == ["2026-03-01"]
        # The stale message is still listed, just without a signal.
        assert [m["signal"] for m in parsed["messages"]] == ["reorganization", None]

    def test_liquidation_decision_has_no_freshness_window(self):
        message = _message(
            "Ликвидация юридического лица",
            publisher=DEBTOR,
            participants=(DEBTOR,),
            date="2019-01-01T00:00:00",
        )
        assert len(parse_publications(_page(message), DEBTOR, today=TODAY)["signals"]) == 1

    def test_unknown_message_type_is_listed_without_a_signal(self):
        message = _message("Стоимость чистых активов", publisher=DEBTOR, participants=(DEBTOR,))
        parsed = parse_publications(_page(message), DEBTOR, today=TODAY)
        assert parsed["signals"] == []
        assert len(parsed["messages"]) == 1


class TestTruncation:
    def test_a_longer_feed_than_the_page_is_flagged_not_treated_as_complete(self):
        parsed = parse_publications(_page(_message(), found=1001), DEBTOR, today=TODAY)
        assert parsed["truncated"] is True
        assert "1001" in parsed["note"]
        # What was found stays valid.
        assert len(parsed["signals"]) == 1


class TestSchemaDrift:
    @pytest.mark.parametrize(
        "broken",
        [
            {},
            {"pageData": "x", "found": 1},
            {"pageData": [], "found": "many"},
            {"pageData": [_message()], "found": 0},
            _page({"type": CREDITOR_INTENT}),
            _page(_message(date="not-a-date")),
            _page(_message(date="2027-01-01T00:00:00", type_="Реорганизация юридического лица")),
        ],
    )
    def test_drifted_payload_raises(self, broken):
        with pytest.raises(FedresursError, match="схема ответа изменилась"):
            parse_publications(broken, DEBTOR, today=TODAY)


class TestClassifyStatus:
    @pytest.mark.parametrize(
        "text, kind",
        [
            ("Действующее", "clean"),
            ("В отношении юридического лица введено наблюдение", "active_bankruptcy"),
            ("Признано банкротом, открыто конкурсное производство", "active_bankruptcy"),
            ("Дело о банкротстве: производство прекращено", "resolved"),
            ("Конкурсное производство завершено", "resolved"),
            ("Ликвидировано", "unrecognized"),
            ("", "unrecognized"),
            (None, "unrecognized"),
        ],
    )
    def test_classification(self, text, kind):
        assert classify_status(text) == kind


SEARCH_ROW = {"guid": BANK, "inn": "7707083893", "name": "ПАО СБЕРБАНК", "status": "Действующее"}


def _handler(search, publications=None, publications_status=200):
    def handler(request):
        if request.url.path.endswith("/publications"):
            if publications_status != 200:
                return httpx.Response(publications_status, text="x")
            return httpx.Response(200, json=publications)
        return httpx.Response(200, json=search)

    return handler


class TestFetchIntegration:
    def test_status_survives_a_blocked_publications_step(self, patch_httpx_transport):
        patch_httpx_transport(
            _handler({"pageData": [SEARCH_ROW], "found": 1}, publications_status=451)
        )
        result, _ = _run(fetch_fedresurs_status("7707083893", is_individual=False))
        assert result["found"] is True
        assert result["publications_checked"] is False
        assert "не проверены" in result["publications_note"]

    def test_signals_flow_into_the_result_and_raw_keeps_both_payloads(self, patch_httpx_transport):
        row = {**SEARCH_ROW, "guid": DEBTOR, "inn": "7702000000", "status": "Действующее"}
        publications = _page(_message())
        patch_httpx_transport(_handler({"pageData": [row], "found": 1}, publications))
        result, raw = _run(fetch_fedresurs_status("7702000000", is_individual=False))
        assert [s["code"] for s in result["signals"]] == ["creditor_bankruptcy_intent"]
        assert '"publications"' in raw and "Намерение кредитора" in raw

    def test_unrecognized_status_is_reported_not_swallowed(self, patch_httpx_transport):
        row = {**SEARCH_ROW, "status": "Какой-то новый статус"}
        patch_httpx_transport(_handler({"pageData": [row], "found": 1}, _page()))
        result, _ = _run(fetch_fedresurs_status("7707083893", is_individual=False))
        assert result["status_recognized"] is False
        assert result["is_active_bankruptcy"] is False

    def test_truncated_search_without_the_exact_inn_is_an_error_not_a_clean_not_found(
        self, patch_httpx_transport
    ):
        rows = [
            {"guid": str(i), "inn": f"00000000{i:02d}", "status": "Действующее"} for i in range(15)
        ]
        patch_httpx_transport(_handler({"pageData": rows, "found": 40}))
        with pytest.raises(FedresursError, match="усечена"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_search_without_a_found_counter_cannot_prove_absence(self, patch_httpx_transport):
        patch_httpx_transport(_handler({"pageData": []}))
        with pytest.raises(FedresursError, match="усечена или без счётчика"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_search_row_missing_status_is_schema_drift(self, patch_httpx_transport):
        row = {"guid": BANK, "inn": "7707083893"}
        patch_httpx_transport(_handler({"pageData": [row], "found": 1}))
        with pytest.raises(FedresursError, match="нет поля «status»"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_non_json_search_response_is_a_clean_error(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text="<html>captcha</html>"))
        with pytest.raises(FedresursError, match="не-JSON"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_401_on_search_is_treated_as_blocked(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(401, text="x"))
        with pytest.raises(FedresursBlocked):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_network_errors_become_fedresurs_errors(self, patch_httpx_transport):
        def boom(request):
            raise httpx.ConnectTimeout("timeout")

        patch_httpx_transport(boom)
        with pytest.raises(FedresursError, match="недоступен"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))


class TestIsFullyChecked:
    @pytest.mark.parametrize(
        "result, is_individual, expected",
        [
            ({"checked": False}, False, False),
            ({"checked": True, "found": False}, False, True),
            ({"checked": True, "found": True, "publications_checked": True}, False, True),
            ({"checked": True, "found": True, "publications_checked": False}, False, False),
            ({"checked": True, "found": True, "publications_checked": False}, True, True),
        ],
    )
    def test_publications_must_be_read_for_a_found_legal_entity(
        self, result, is_individual, expected
    ):
        assert is_fully_checked(result, is_individual=is_individual) is expected
