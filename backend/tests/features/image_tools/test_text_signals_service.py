from app.features.image_tools.service.text_signals_service import compute_text_signals


def _by_kind(signals, kind):
    return [s for s in signals if s.kind == kind]


def test_empty_and_blank_lines_yield_nothing():
    assert compute_text_signals([]) == []
    assert compute_text_signals(["", "   "]) == []


def test_plain_latin_text_has_no_script_or_country_signals():
    signals = compute_text_signals(["Main 24"])
    assert signals == []


def test_script_points_to_its_countries():
    signals = compute_text_signals(["กรุงเทพ"])
    thai = _by_kind(signals, "script")
    assert thai[0].matched == "Thai"
    assert thai[0].countries == ["TH"]


def test_cyrillic_is_a_shared_script_with_letter_narrowing_the_language():
    signals = compute_text_signals(["Київ"])
    assert "RU" in _by_kind(signals, "script")[0].countries
    assert _by_kind(signals, "letter")[0].languages == ["uk"]


def test_non_western_digits_are_reported_but_ascii_digits_are_not():
    assert _by_kind(compute_text_signals(["۱۲۳"]), "digits")
    assert not _by_kind(compute_text_signals(["123"]), "digits")


def test_phone_country_code_resolves_unique_prefix():
    signals = compute_text_signals(["Tel +351 21 342 0000"])
    phone = _by_kind(signals, "phone")[0]
    assert phone.countries == ["PT"]
    assert phone.strength == "strong"


def test_shared_calling_code_is_too_weak_to_report():
    assert _by_kind(compute_text_signals(["+1 202 555 0100"]), "phone") == []
    assert _by_kind(compute_text_signals(["+7 495 123 45 67"]), "phone")


def test_country_tld_maps_to_country_but_vanity_tld_does_not():
    assert _by_kind(compute_text_signals(["www.loja.com.br"]), "domain")[0].countries == ["BR"]
    assert _by_kind(compute_text_signals(["bit.ly", "site.io", "my.tv"]), "domain") == []


def test_alphabetic_currency_mark_needs_an_adjacent_number():
    assert _by_kind(compute_text_signals(["Cena 25 zł"]), "currency")
    assert not _by_kind(compute_text_signals(["Q is a letter"]), "currency")


def test_regional_word_with_country_is_strong_and_accents_are_ignored():
    signals = compute_text_signals(["TALHO"])
    word = _by_kind(signals, "word")[0]
    assert word.countries == ["PT"]
    assert word.strength == "strong"


def test_word_must_match_whole_words():
    assert _by_kind(compute_text_signals(["Talhosa"]), "word") == []


def test_signals_are_deduplicated_across_lines():
    signals = compute_text_signals(["Київ", "Харків", "Львів"])
    assert len(_by_kind(signals, "script")) == 1


def test_signal_count_per_kind_is_capped():
    lines = [f"{c}" for c in "ąćęłńóśźżőűßçñøåäö"]
    assert len(_by_kind(compute_text_signals(lines), "letter")) <= 8


def test_same_letter_in_both_cases_is_one_signal():
    assert len(_by_kind(compute_text_signals(["Ђорђе"]), "letter")) == 1


def test_oversized_transcription_is_bounded():
    from app.features.image_tools.service import text_signals_service as svc

    lines = ["ł"] * 5 + ["x" * 10] * svc._MAX_LINES + ["ő"]
    kinds = {s.matched for s in compute_text_signals(lines)}
    assert "ł" in kinds
    assert "ő" not in kinds  # past the line cap

    long_line = "x" * svc._MAX_LINE_LENGTH + "ő"
    assert _by_kind(compute_text_signals([long_line]), "letter") == []


def test_signals_are_ordered_strongest_first():
    signals = compute_text_signals(["Київ", "+351 21 342 0000", "3,50€"])
    ranks = [{"strong": 0, "medium": 1, "weak": 2}[s.strength] for s in signals]
    assert ranks == sorted(ranks)
    assert signals[0].kind == "phone"
