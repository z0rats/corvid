from app.features.dork_runner.config.dork_templates import (
    DORK_TEMPLATES,
    get_template_by_key,
    get_templates_for_target_type,
)


class TestDorkTemplatesLibrary:
    def test_every_template_key_is_unique(self):
        keys = [t.key for t in DORK_TEMPLATES]
        assert len(keys) == len(set(keys))

    def test_every_pattern_has_a_target_placeholder_and_is_formattable(self):
        for template in DORK_TEMPLATES:
            assert "{target}" in template.pattern
            # Would raise (KeyError/IndexError) if the pattern referenced any
            # placeholder other than `target`.
            template.pattern.format(target="example.com")

    def test_every_template_declares_at_least_one_target_type(self):
        for template in DORK_TEMPLATES:
            assert len(template.target_types) > 0


class TestGetTemplatesForTargetType:
    def test_domain_only_templates_are_excluded_for_username(self):
        domain_keys = {t.key for t in get_templates_for_target_type("domain")}
        username_keys = {t.key for t in get_templates_for_target_type("username")}

        assert "site_search" in domain_keys
        assert "site_search" not in username_keys

    def test_a_template_applicable_to_multiple_target_types_appears_in_each(self):
        for target_type in ("domain", "username", "email"):
            keys = {t.key for t in get_templates_for_target_type(target_type)}
            assert "generic_mentions" in keys

    def test_unknown_target_type_returns_no_templates(self):
        assert get_templates_for_target_type("not-a-real-type") == []


class TestGetTemplateByKey:
    def test_returns_the_matching_template(self):
        template = get_template_by_key("site_search")
        assert template is not None
        assert template.pattern == "site:{target}"

    def test_returns_none_for_an_unknown_key(self):
        assert get_template_by_key("does-not-exist") is None
