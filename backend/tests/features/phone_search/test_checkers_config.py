from app.features.phone_search.config.checkers_config import (
    CHECKERS,
    amazon_checker,
    facebook_checker,
    get_active_checkers,
    microsoft_checker,
)


class TestGetActiveCheckers:
    def test_returns_all_three_phase_one_checkers(self):
        checkers = get_active_checkers()
        assert checkers == [amazon_checker, microsoft_checker, facebook_checker]

    def test_returns_a_copy_not_the_shared_list(self):
        checkers = get_active_checkers()
        checkers.append("mutated")
        assert CHECKERS == [amazon_checker, microsoft_checker, facebook_checker]

    def test_every_checker_exposes_the_shared_contract(self):
        for checker in CHECKERS:
            assert isinstance(checker.PROVIDER_NAME, str) and checker.PROVIDER_NAME
            assert callable(checker.check)
