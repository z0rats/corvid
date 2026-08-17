"""Plain default values for email_search settings.

Kept import-light (no `mailcat` import) on purpose: the settings model
(`app/core/settings/email_search/models/email_search_settings_models.py`) reads these for
its column defaults, and that model module is imported by every `alembic upgrade head` run
plus at every app startup - pulling in `mailcat_config.py` there would drag its
`requests-html`/`pyppeteer` headless-Chromium chain along just to read five int/bool
literals.
"""

TIMEOUT_SECONDS_DEFAULT = 10
MAX_CONCURRENCY_DEFAULT = 10
USE_TOR_DEFAULT = False
ENABLE_SMTP_CHECKS_DEFAULT = False
ENABLE_HEADLESS_CHECKS_DEFAULT = False
