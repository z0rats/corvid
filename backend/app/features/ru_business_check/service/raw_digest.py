"""SHA-256 fingerprints of each source's verbatim payload, taken at capture time.

Stored next to the payloads (`raw_sha256`) rather than derived when displayed: a hash
recomputed from the stored text at read time would agree with any edit of that text, while
one recorded at scan time lets the stored copy - or an independently saved export of it - be
checked later (`sha256sum` of the raw text must match). It fingerprints what this instance
received; it is not a timestamp authority and doesn't prove what the remote site served.
"""

import hashlib


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_payloads(payloads: dict[str, str | None]) -> dict[str, str]:
    """`{source: verbatim payload}` -> `{source: sha256}`, omitting sources with no payload
    (not queried / failed)."""
    return {source: sha256_hex(text) for source, text in payloads.items() if text}
