from app.features.ioc_tools.domain_finder.utils.subdomain_utils import subdomains_of


def test_keeps_the_domain_and_names_under_it():
    names = ["example.com", "www.example.com", "a.b.example.com"]

    assert subdomains_of(names, "example.com") == set(names)


def test_drops_unrelated_and_look_alike_names():
    names = ["example.org", "notexample.com", "example.com.evil.net", ""]

    assert subdomains_of(names, "example.com") == set()


def test_normalizes_case_whitespace_and_a_leading_wildcard():
    names = [" WWW.Example.COM ", "*.dev.example.com", "*.example.com"]

    assert subdomains_of(names, "example.com") == {
        "www.example.com",
        "dev.example.com",
        "example.com",
    }
