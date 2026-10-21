"""The MITRE enrichment is the LLM's structured output over third-party article
text, so its URLs are attacker-influenceable (prompt injection). Only real
ATT&CK links may survive validation - anything else is dropped to None."""

import pytest

from app.features.newsfeed.schemas.newsfeed_schemas import ThreatIntelEnrichment

GOOD = "https://attack.mitre.org/techniques/T1566/001/"


def _enrichment(url: str | None) -> ThreatIntelEnrichment:
    ref = {"name": "Phishing", "id": "T1566", "url": url}
    return ThreatIntelEnrichment.model_validate(
        {
            "has_mitre_data": True,
            "threat_actors": [{"name": "APT29", "mitre_url": url}],
            "software": [{"name": "Cobalt Strike", "type": "tool", "mitre_url": url}],
            "ttps": [
                {
                    "tactic": {"name": "Initial Access", "id": "TA0001", "url": url},
                    "technique": ref,
                    "sub_technique": {**ref, "id": "T1566.001"},
                }
            ],
        }
    )


def _urls(e: ThreatIntelEnrichment) -> list[str | None]:
    ttp = e.ttps[0]
    return [
        e.threat_actors[0].mitre_url,
        e.software[0].mitre_url,
        ttp.tactic.url,
        ttp.technique.url,
        ttp.sub_technique.url,
    ]


def test_attack_mitre_org_links_are_kept():
    assert _urls(_enrichment(GOOD)) == [GOOD] * 5


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/attack.mitre.org/",
        "https://attack.mitre.org.evil.example/techniques/T1566/",
        "http://attack.mitre.org/techniques/T1566/",
        "javascript:alert(document.cookie)",
        "//attack.mitre.org/x",
        "",
        None,
    ],
)
def test_anything_else_is_dropped(url):
    assert _urls(_enrichment(url)) == [None] * 5
