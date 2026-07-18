# Tunables for the git_recon feature (gitcolombo integration). Hardcoded
# rather than a persisted settings module - like reddit_search, there's
# nothing here meaningfully worth letting the analyst tune per-deployment.

# Full (non-shallow) clones are required - gitcolombo walks `git log --all`
# for author/committer history, which a shallow clone would truncate. Caps
# worst-case disk/time for 'nickname' mode, where a very active account can
# have hundreds of public repos.
MAX_REPOS_PER_SCAN = 25

CLONE_WORKERS = 8

# Hard ceiling on total scan time (cloning + git log + optional GitHub-login
# resolution), independent of any per-call network timeout inside gitcolombo
# itself. Mirrors social_analyzer_config.py's PROCESS_WATCHDOG_SECONDS.
WALL_CLOCK_TIMEOUT_SECONDS = 300
