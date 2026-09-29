"""opensanctions_csv_parser against the live column shape captured 2026-09-29 (16 columns,
only a subset needed here; extras like birth_date/addresses/identifiers/phones/emails/dataset/
last_change are ignored rather than rejected)."""

import datetime

import pytest

from app.features.sanctions_search.service.opensanctions_csv_parser import (
    OpenSanctionsCsvError,
    parse_targets_csv,
)

HEADER = (
    "id,schema,name,aliases,birth_date,countries,addresses,identifiers,sanctions,phones,"
    "emails,program_ids,dataset,first_seen,last_seen,last_change"
)


def _row(
    id_="NK-1",
    schema="Person",
    name="Jane Doe",
    aliases="Jane D.;J. Doe",
    countries="us;ru",
    sanctions="GLOMAG - Executive Order 13818",
    program_ids="US-GLOMAG",
    first_seen="2024-05-01T18:10:01",
    last_seen="2026-09-29T08:10:01",
):
    return (
        f'"{id_}","{schema}","{name}","{aliases}","","{countries}","","","{sanctions}","","",'
        f'"{program_ids}","US OFAC Specially Designated Nationals (SDN) List","{first_seen}",'
        f'"{last_seen}","2026-01-26T16:10:01"'
    )


def test_parses_a_well_formed_row():
    text = HEADER + "\n" + _row() + "\n"
    records, total = parse_targets_csv(text)
    assert total == 1
    assert records == [
        {
            "opensanctions_id": "NK-1",
            "schema": "Person",
            "name": "Jane Doe",
            "aliases": ["Jane D.", "J. Doe"],
            "countries": ["us", "ru"],
            "programs": ["US-GLOMAG"],
            "sanctions": "GLOMAG - Executive Order 13818",
            "first_seen": datetime.date(2024, 5, 1),
            "last_seen": datetime.date(2026, 9, 29),
        }
    ]


def test_empty_multi_value_fields_become_empty_lists():
    text = HEADER + "\n" + _row(aliases="", countries="", program_ids="") + "\n"
    records, _total = parse_targets_csv(text)
    assert records[0]["aliases"] == []
    assert records[0]["countries"] == []
    assert records[0]["programs"] == []


def test_multi_value_fields_dedupe_preserving_order():
    text = HEADER + "\n" + _row(aliases="A;B;A;C;B") + "\n"
    records, _total = parse_targets_csv(text)
    assert records[0]["aliases"] == ["A", "B", "C"]


def test_a_row_missing_id_or_name_is_skipped_but_still_counted():
    rows = [_row(id_="NK-2"), _row(name=""), _row(id_="")]
    text = HEADER + "\n" + "\n".join(rows) + "\n"
    records, total = parse_targets_csv(text)
    assert total == 3
    assert len(records) == 1
    assert records[0]["opensanctions_id"] == "NK-2"


def test_missing_required_column_raises():
    bad_header = HEADER.replace("program_ids,", "")
    text = bad_header + "\n" + _row() + "\n"
    with pytest.raises(OpenSanctionsCsvError, match="missing columns"):
        parse_targets_csv(text)


def test_a_sanctions_field_over_the_length_cap_is_truncated():
    long_text = "x" * 3000
    text = HEADER + "\n" + _row(sanctions=long_text) + "\n"
    records, _total = parse_targets_csv(text)
    assert len(records[0]["sanctions"]) == 2000
