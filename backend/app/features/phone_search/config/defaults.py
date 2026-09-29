"""Plain default values for phone_search settings.

Kept import-light on purpose, same rationale as email_search/config/defaults.py: the
settings model reads these for its column defaults and is imported at every app
startup/migration run.
"""

TIMEOUT_SECONDS_DEFAULT = 10
