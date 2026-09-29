"""When a live canary may skip rather than fail - kept apart from the canary tests so the
normal suite can pin it (`tests/features/ru_business_check/test_source_contract.py`)."""

import re

# Only "the site didn't answer *us*": network, anti-bot/geo status, server error, captcha,
# rate limit. Matched against the source clients' own error messages. Everything else fails -
# schema drift, a JSON endpoint answering HTML, and an unexpected empty/partial answer
# ("Ничего не найдено", "выдача усечена"), since the reference ИНН are known to have data.
UNREACHABLE = re.compile(
    r"недоступен|ограничил доступ|капч|лимит запросов|не ответил|Тайм-аут"
    r"|HTTP (?:401|403|429|451|5\d\d)\b"
)
