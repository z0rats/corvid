"""Weights, thresholds and lexicon for the CS2 cheater-probability heuristic
(`service/steam_cheater_scoring_service.py`).

This is a transparent weighted-signal logit, not a trained model: SteamReveal's own ML
classifier and its training data aren't available to reproduce (see
docs/adr/0014-steam-recon-clean-room-and-heuristic-scoring.md), so probability here means
"how well the profile matches known suspicious patterns", each pattern's contribution shown
separately - not a calibrated probability of guilt.
"""

CS2_APPID = 730

# probability = sigmoid(BIAS + sum(weight * signal_value)), signal_value in [0, 1].
# A negative BIAS means "innocent until enough signals fire" - a profile with every signal
# at 0 (or unavailable) should land near 0.1, not 0.5.
LOGIT_BIAS = -3.5

SIGNAL_WEIGHTS = {
    "own_vac_or_game_ban": 3.0,
    "friend_ban_density": 2.5,
    "low_account_investment": 1.2,
    "stat_outliers": 2.0,
    "accusatory_comments": 1.5,
}

# --- own_vac_or_game_ban -----------------------------------------------------------------
# A ban within the last N days counts fully; older bans decay linearly to a floor, since a
# years-old ban says less about current behaviour than a recent one.
BAN_RECENCY_FULL_WEIGHT_DAYS = 180
BAN_RECENCY_FLOOR_DAYS = 1095  # 3 years
BAN_RECENCY_FLOOR_VALUE = 0.3

# --- low_account_investment --------------------------------------------------------------
# An account below every one of these looks "thrown together" (a smurf/throwaway pattern) -
# each unmet threshold contributes 1/3 to the signal.
LOW_INVESTMENT_MIN_ACCOUNT_AGE_DAYS = 365
LOW_INVESTMENT_MIN_LEVEL = 10
LOW_INVESTMENT_MIN_GAMES = 5

# --- stat_outliers -------------------------------------------------------------------------
# Values at/above these look statistically implausible for organic play; the signal scales
# linearly from 0 at the threshold's midpoint to 1 at the threshold itself, so a stat just
# over a "normal" range doesn't immediately max out the signal.
STAT_THRESHOLDS = {
    "headshot_ratio": 0.65,  # kills-with-headshot / total kills
    "accuracy": 0.35,  # shots-hit / shots-fired
    "kd_ratio": 3.0,  # kills / deaths
}
# Below this many total rounds, per-match stats are too noisy to score at all.
STAT_MIN_ROUNDS_PLAYED = 200

# --- accusatory_comments -------------------------------------------------------------------
# Case-insensitive substrings across the languages this repo already supports UI text in
# (en/ru/pt/de/es) plus a few universal terms. Matches by substring, not whole-word, since
# leetspeak/spacing variants ("h4ck", "che at") are common in accusatory comments.
ACCUSATION_LEXICON = (
    # English
    "cheat",
    "cheater",
    "hacker",
    "hacking",
    "wallhack",
    "wall hack",
    "aimbot",
    "aim bot",
    "vac ban",
    "smurf",
    "rage hack",
    "legit hack",
    # Russian
    "чит",
    "читер",
    "хакер",
    "хак",
    "валхак",
    "аимбот",
    "спинбот",
    "вак бан",
    # Portuguese
    "hacker",
    "aimbot",
    "cheat",
    "vac banido",
    # German
    "cheater",
    "hacker",
    "wallhack",
    "betrüger",
    # Spanish
    "tramposo",
    "hacker",
    "cheater",
    "aimbot",
)
# Minimum comments (excluding the target's own) before this signal is scored at all -
# a couple of comments isn't enough of a sample either way.
MIN_COMMENTS_FOR_SIGNAL = 5

# --- overall probability -> level ---------------------------------------------------------
PROBABILITY_LEVEL_MEDIUM_THRESHOLD = 0.3
PROBABILITY_LEVEL_HIGH_THRESHOLD = 0.6
