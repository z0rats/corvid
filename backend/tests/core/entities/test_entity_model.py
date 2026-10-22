import pytest

from app.core.entities.model import Extraction, entity, normalize


@pytest.mark.parametrize(
    ("entity_type", "raw", "expected"),
    [
        ("domain", "Example.COM.", "example.com"),
        ("domain", "пример.рф", "xn--e1afmkfd.xn--p1ai"),
        ("email", " J.Doe@Example.com ", "j.doe@example.com"),
        ("username", "@JDoe", "jdoe"),
        ("username", "u/JDoe", "jdoe"),
        ("subreddit", "Python", "python"),
        ("asn", "as13335", "AS13335"),
        ("cve", "cve-2024-1234", "CVE-2024-1234"),
        ("hash", "ABCDEF", "abcdef"),
        ("account", "https://GitHub.com/JDoe/", "https://github.com/jdoe"),
        ("url", "HTTPS://Example.com/Path/?q=1#frag", "https://example.com/Path?q=1"),
        ("account", "GitHub/j@x.com", "github/j@x.com"),
        ("wallet", "0xAbCd", "0xabcd"),
        ("wallet", "1BoatSLRHtKNngkdXEeobR76b53LETtpyT", "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"),
    ],
)
def test_normalize(entity_type, raw, expected):
    assert normalize(entity_type, raw) == expected


def test_same_normalized_value_is_one_entity_whatever_the_label():
    assert entity("username", "JDoe", "u/JDoe") == entity("username", "jdoe")
    assert entity("username", "JDoe").id == "username:jdoe"


def test_label_defaults_to_the_raw_value():
    assert entity("domain", " Example.com ").label == "Example.com"


def test_raw_value_keeps_the_sources_case():
    account = entity("account", " https://GitHub.com/JDoe ")
    assert (account.value, account.raw) == ("https://github.com/jdoe", "https://GitHub.com/JDoe")


def test_link_skips_self_links():
    out = Extraction(root=None)
    node = entity("username", "a")
    out.link(node, entity("username", "A"), "same")
    assert out.links == []


def test_link_local_part_strips_plus_tag():
    email = entity("email", "j.doe+news@x.com")
    out = Extraction(root=email)
    out.link_local_part(email)
    assert [(link.target.id, link.relation) for link in out.links] == [
        ("username:j.doe", "local part")
    ]
