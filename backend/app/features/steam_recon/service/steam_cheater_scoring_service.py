"""CS2 cheater-probability heuristic: a transparent weighted-signal logit over five signals,
each independently explainable, rather than a trained model (see cheater_scoring_config.py's
module docstring for why). Every signal that has no usable data contributes nothing to the
probability rather than being treated as innocent or guilty - `coverage` on the result says how
much of the picture was actually available.
"""

import dataclasses
import math

from app.features.steam_recon.config.cheater_scoring_config import (
    BAN_RECENCY_FLOOR_DAYS,
    BAN_RECENCY_FLOOR_VALUE,
    BAN_RECENCY_FULL_WEIGHT_DAYS,
    LOGIT_BIAS,
    LOW_INVESTMENT_MIN_ACCOUNT_AGE_DAYS,
    LOW_INVESTMENT_MIN_GAMES,
    LOW_INVESTMENT_MIN_LEVEL,
    MIN_COMMENTS_FOR_SIGNAL,
    PROBABILITY_LEVEL_HIGH_THRESHOLD,
    PROBABILITY_LEVEL_MEDIUM_THRESHOLD,
    SIGNAL_WEIGHTS,
    STAT_MIN_ROUNDS_PLAYED,
    STAT_THRESHOLDS,
)
from app.features.steam_recon.schemas.steam_recon_schemas import SteamBans
from app.features.steam_recon.service.steam_graph_service import FriendCandidate


@dataclasses.dataclass
class SignalResult:
    id: str
    value: float | None  # None = no usable data for this signal
    weight: float
    contribution: float  # weight * value, or 0.0 when value is None
    explanation: str


@dataclasses.dataclass
class CheaterReport:
    probability: float
    level: str  # "low" | "medium" | "high"
    coverage: float  # fraction of signals with usable data
    already_banned: bool
    signals: list[SignalResult]


def _score_own_ban(bans: SteamBans | None) -> SignalResult:
    if bans is None:
        return SignalResult(
            "own_vac_or_game_ban",
            None,
            SIGNAL_WEIGHTS["own_vac_or_game_ban"],
            0.0,
            "Ban record unavailable",
        )
    if not bans.vac_banned and bans.number_of_game_bans == 0:
        return SignalResult(
            "own_vac_or_game_ban",
            0.0,
            SIGNAL_WEIGHTS["own_vac_or_game_ban"],
            0.0,
            "No VAC or game ban on record",
        )

    days = bans.days_since_last_ban
    if days <= BAN_RECENCY_FULL_WEIGHT_DAYS:
        value = 1.0
    elif days >= BAN_RECENCY_FLOOR_DAYS:
        value = BAN_RECENCY_FLOOR_VALUE
    else:
        span = BAN_RECENCY_FLOOR_DAYS - BAN_RECENCY_FULL_WEIGHT_DAYS
        value = 1.0 - (1.0 - BAN_RECENCY_FLOOR_VALUE) * (days - BAN_RECENCY_FULL_WEIGHT_DAYS) / span

    total_bans = bans.number_of_vac_bans + bans.number_of_game_bans
    explanation = f"{total_bans} ban(s) on record, most recent {days} days ago"
    weight = SIGNAL_WEIGHTS["own_vac_or_game_ban"]
    return SignalResult("own_vac_or_game_ban", value, weight, weight * value, explanation)


def _score_friend_ban_density(candidates: list[FriendCandidate]) -> SignalResult:
    weight = SIGNAL_WEIGHTS["friend_ban_density"]
    connected = [c for c in candidates if c.mutual_count > 0]
    total_weight = sum(c.mutual_count for c in connected)
    if not connected or total_weight == 0:
        return SignalResult(
            "friend_ban_density", None, weight, 0.0, "No connected friends to evaluate"
        )

    banned_weight = sum(
        c.mutual_count
        for c in connected
        if c.bans and (c.bans.get("VACBanned") or c.bans.get("NumberOfGameBans", 0) > 0)
    )
    value = banned_weight / total_weight
    explanation = f"{value:.0%} of close-friend weight carries a VAC/game ban"
    return SignalResult("friend_ban_density", value, weight, weight * value, explanation)


def _score_low_investment(
    account_age_days: int | None, level: int | None, game_count: int | None
) -> SignalResult:
    weight = SIGNAL_WEIGHTS["low_account_investment"]
    checks = []
    if account_age_days is not None:
        checks.append(account_age_days < LOW_INVESTMENT_MIN_ACCOUNT_AGE_DAYS)
    if level is not None:
        checks.append(level < LOW_INVESTMENT_MIN_LEVEL)
    if game_count is not None:
        checks.append(game_count < LOW_INVESTMENT_MIN_GAMES)

    if not checks:
        return SignalResult(
            "low_account_investment", None, weight, 0.0, "Account investment data unavailable"
        )

    value = sum(checks) / len(checks)
    explanation = f"{sum(checks)}/{len(checks)} low-investment thresholds met (age/level/games)"
    return SignalResult("low_account_investment", value, weight, weight * value, explanation)


def _scale(value: float, threshold: float) -> float:
    """0 at 70% of the threshold, 1 at the threshold, clipped to [0, 1]."""
    low = threshold * 0.7
    if value <= low:
        return 0.0
    if value >= threshold:
        return 1.0
    return (value - low) / (threshold - low)


def _score_stat_outliers(stats: dict[str, int] | None) -> SignalResult:
    weight = SIGNAL_WEIGHTS["stat_outliers"]
    if not stats or stats.get("total_rounds_played", 0) < STAT_MIN_ROUNDS_PLAYED:
        return SignalResult(
            "stat_outliers", None, weight, 0.0, "CS2 stats unavailable or too few rounds played"
        )

    kills = stats.get("total_kills", 0)
    deaths = stats.get("total_deaths", 0) or 1
    headshots = stats.get("total_kills_headshot", 0)
    shots_fired = stats.get("total_shots_fired", 0) or 1
    shots_hit = stats.get("total_shots_hit", 0)

    hs_ratio = headshots / kills if kills else 0.0
    accuracy = shots_hit / shots_fired
    kd_ratio = kills / deaths

    sub_scores = {
        "headshot_ratio": _scale(hs_ratio, STAT_THRESHOLDS["headshot_ratio"]),
        "accuracy": _scale(accuracy, STAT_THRESHOLDS["accuracy"]),
        "kd_ratio": _scale(kd_ratio, STAT_THRESHOLDS["kd_ratio"]),
    }
    value = max(sub_scores.values())
    explanation = (
        f"HS {hs_ratio:.0%}, accuracy {accuracy:.0%}, K/D {kd_ratio:.1f} vs "
        f"thresholds {STAT_THRESHOLDS['headshot_ratio']:.0%}/"
        f"{STAT_THRESHOLDS['accuracy']:.0%}/{STAT_THRESHOLDS['kd_ratio']:.1f}"
    )
    return SignalResult("stat_outliers", value, weight, weight * value, explanation)


def _score_accusatory_comments(ratio: float | None, sample_size: int) -> SignalResult:
    weight = SIGNAL_WEIGHTS["accusatory_comments"]
    if ratio is None or sample_size < MIN_COMMENTS_FOR_SIGNAL:
        return SignalResult(
            "accusatory_comments", None, weight, 0.0, "Not enough comments to evaluate"
        )
    explanation = f"{ratio:.0%} of {sample_size} comments (excl. the profile owner) look accusatory"
    return SignalResult("accusatory_comments", ratio, weight, weight * ratio, explanation)


def _level(probability: float) -> str:
    if probability >= PROBABILITY_LEVEL_HIGH_THRESHOLD:
        return "high"
    if probability >= PROBABILITY_LEVEL_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def compute_cheater_report(
    *,
    bans: SteamBans | None,
    candidates: list[FriendCandidate],
    account_age_days: int | None,
    level: int | None,
    game_count: int | None,
    cs2_stats: dict[str, int] | None,
    accusatory_ratio: float | None,
    accusatory_sample_size: int,
) -> CheaterReport:
    signals = [
        _score_own_ban(bans),
        _score_friend_ban_density(candidates),
        _score_low_investment(account_age_days, level, game_count),
        _score_stat_outliers(cs2_stats),
        _score_accusatory_comments(accusatory_ratio, accusatory_sample_size),
    ]

    logit = LOGIT_BIAS + sum(s.contribution for s in signals)
    probability = 1 / (1 + math.exp(-logit))
    coverage = sum(1 for s in signals if s.value is not None) / len(signals)
    already_banned = bool(bans and (bans.vac_banned or bans.number_of_game_bans > 0))

    return CheaterReport(
        probability=probability,
        level=_level(probability),
        coverage=coverage,
        already_banned=already_banned,
        signals=signals,
    )
