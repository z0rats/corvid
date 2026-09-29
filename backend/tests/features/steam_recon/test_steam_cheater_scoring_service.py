from app.features.steam_recon.schemas.steam_recon_schemas import SteamBans
from app.features.steam_recon.service.steam_cheater_scoring_service import compute_cheater_report
from app.features.steam_recon.service.steam_graph_service import FriendCandidate

CLEAN_BANS = SteamBans(
    community_banned=False,
    vac_banned=False,
    number_of_vac_bans=0,
    days_since_last_ban=0,
    number_of_game_bans=0,
    economy_ban="none",
)


def _candidate(steamid, mutual_count, banned=False):
    return FriendCandidate(
        steamid64=steamid,
        persona_name=steamid,
        avatar_url=None,
        friend_since=None,
        country_code=None,
        state_code=None,
        city_id=None,
        mutual_count=mutual_count,
        friends_private=False,
        bans={"VACBanned": banned, "NumberOfGameBans": 0} if mutual_count else None,
    )


def _base_kwargs(**overrides):
    kwargs = dict(
        bans=CLEAN_BANS,
        candidates=[],
        account_age_days=2000,
        level=50,
        game_count=100,
        cs2_stats=None,
        accusatory_ratio=None,
        accusatory_sample_size=0,
    )
    kwargs.update(overrides)
    return kwargs


def test_a_totally_clean_profile_scores_low_with_full_coverage_except_stats_and_comments():
    report = compute_cheater_report(**_base_kwargs())

    assert report.level == "low"
    assert report.probability < 0.3
    assert report.already_banned is False
    # only own_vac_or_game_ban and low_account_investment have data in this fixture
    # (no candidates -> no friend_ban_density; no CS2 stats/comments either)
    assert report.coverage == 2 / 5


def test_no_data_at_all_still_lands_low_not_neutral():
    report = compute_cheater_report(
        bans=None,
        candidates=[],
        account_age_days=None,
        level=None,
        game_count=None,
        cs2_stats=None,
        accusatory_ratio=None,
        accusatory_sample_size=0,
    )

    assert report.coverage == 0.0
    assert report.level == "low"
    assert report.probability < 0.2


def test_own_recent_ban_is_flagged_and_raises_probability():
    banned = SteamBans(
        community_banned=False,
        vac_banned=True,
        number_of_vac_bans=1,
        days_since_last_ban=10,
        number_of_game_bans=0,
        economy_ban="none",
    )
    clean = compute_cheater_report(**_base_kwargs())
    report = compute_cheater_report(**_base_kwargs(bans=banned))

    assert report.already_banned is True
    assert report.probability > clean.probability
    own_ban_signal = next(s for s in report.signals if s.id == "own_vac_or_game_ban")
    assert own_ban_signal.value == 1.0


def test_an_old_ban_contributes_less_than_a_recent_one():
    recent = SteamBans(
        community_banned=False,
        vac_banned=True,
        number_of_vac_bans=1,
        days_since_last_ban=10,
        number_of_game_bans=0,
        economy_ban="none",
    )
    old = SteamBans(
        community_banned=False,
        vac_banned=True,
        number_of_vac_bans=1,
        days_since_last_ban=2000,
        number_of_game_bans=0,
        economy_ban="none",
    )

    recent_report = compute_cheater_report(**_base_kwargs(bans=recent))
    old_report = compute_cheater_report(**_base_kwargs(bans=old))

    assert old_report.probability < recent_report.probability


def test_friend_ban_density_is_weighted_by_mutual_count():
    candidates = [
        _candidate("A", mutual_count=10, banned=True),
        _candidate("B", mutual_count=1, banned=False),
    ]
    report = compute_cheater_report(**_base_kwargs(candidates=candidates))

    signal = next(s for s in report.signals if s.id == "friend_ban_density")
    assert signal.value == 10 / 11


def test_friend_ban_density_ignores_friends_with_zero_mutual_weight():
    candidates = [_candidate("A", mutual_count=0, banned=True)]
    report = compute_cheater_report(**_base_kwargs(candidates=candidates))

    signal = next(s for s in report.signals if s.id == "friend_ban_density")
    assert signal.value is None


def test_low_investment_flags_a_fresh_low_level_account():
    report = compute_cheater_report(**_base_kwargs(account_age_days=5, level=1, game_count=1))

    signal = next(s for s in report.signals if s.id == "low_account_investment")
    assert signal.value == 1.0
    assert report.probability > compute_cheater_report(**_base_kwargs()).probability


def test_stat_outliers_needs_enough_rounds_played():
    report = compute_cheater_report(
        **_base_kwargs(cs2_stats={"total_rounds_played": 10, "total_kills": 100, "total_deaths": 1})
    )

    signal = next(s for s in report.signals if s.id == "stat_outliers")
    assert signal.value is None


def test_stat_outliers_flags_an_implausible_kd_and_headshot_ratio():
    stats = {
        "total_rounds_played": 1000,
        "total_kills": 5000,
        "total_deaths": 500,
        "total_kills_headshot": 4000,
        "total_shots_fired": 10000,
        "total_shots_hit": 3000,
    }
    report = compute_cheater_report(**_base_kwargs(cs2_stats=stats))

    signal = next(s for s in report.signals if s.id == "stat_outliers")
    assert signal.value == 1.0


def test_stat_outliers_scores_ordinary_stats_as_zero():
    stats = {
        "total_rounds_played": 1000,
        "total_kills": 1000,
        "total_deaths": 1000,
        "total_kills_headshot": 300,
        "total_shots_fired": 10000,
        "total_shots_hit": 2000,
    }
    report = compute_cheater_report(**_base_kwargs(cs2_stats=stats))

    signal = next(s for s in report.signals if s.id == "stat_outliers")
    assert signal.value == 0.0


def test_accusatory_comments_needs_a_minimum_sample_size():
    report = compute_cheater_report(**_base_kwargs(accusatory_ratio=1.0, accusatory_sample_size=2))

    signal = next(s for s in report.signals if s.id == "accusatory_comments")
    assert signal.value is None


def test_accusatory_comments_contributes_when_sample_is_large_enough():
    report = compute_cheater_report(**_base_kwargs(accusatory_ratio=0.8, accusatory_sample_size=20))

    signal = next(s for s in report.signals if s.id == "accusatory_comments")
    assert signal.value == 0.8
    assert signal.contribution > 0


def test_probability_is_monotonic_in_every_available_signal():
    baseline = compute_cheater_report(**_base_kwargs())
    worse = compute_cheater_report(
        **_base_kwargs(
            bans=SteamBans(
                community_banned=False,
                vac_banned=True,
                number_of_vac_bans=1,
                days_since_last_ban=5,
                number_of_game_bans=0,
                economy_ban="none",
            ),
            candidates=[_candidate("A", mutual_count=10, banned=True)],
            account_age_days=1,
            level=0,
            game_count=0,
            cs2_stats={
                "total_rounds_played": 1000,
                "total_kills": 5000,
                "total_deaths": 500,
                "total_kills_headshot": 4500,
                "total_shots_fired": 10000,
                "total_shots_hit": 4000,
            },
            accusatory_ratio=0.9,
            accusatory_sample_size=20,
        )
    )

    assert worse.probability > baseline.probability
    assert worse.level == "high"
