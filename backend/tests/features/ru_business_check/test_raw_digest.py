import hashlib

from app.features.ru_business_check.service.raw_digest import digest_payloads, sha256_hex


def test_sha256_matches_the_standard_digest_of_the_utf8_text():
    text = 'ответ: "Действующее"'
    assert sha256_hex(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_sources_without_a_payload_are_omitted_not_hashed_as_empty():
    digests = digest_payloads({"egrul": "x", "fedresurs": "", "rnp": None})
    assert set(digests) == {"egrul"}
