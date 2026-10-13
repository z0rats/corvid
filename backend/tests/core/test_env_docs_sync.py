"""Every environment variable the settings classes read must be documented.

The settings classes in `app/core/config/settings.py` are the source of truth. A variable
added there without a row in the website's configuration page (or an entry in `.env.example`)
is invisible to operators, so this fails until both are updated.
"""

import importlib
from pathlib import Path

import pytest
from pydantic_settings import BaseSettings

# `app.core.config` re-exports the `settings` instance under the same name as the submodule, so a
# plain `import ... as` would bind the instance instead of the module.
settings_module = importlib.import_module("app.core.config.settings")

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIGURATION_DOC = REPO_ROOT / "website/src/content/docs/getting-started/configuration.md"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

# Deliberately absent from .env.example (still documented): `API_VERSION` is stamped at image-build
# time, and `API_DESCRIPTION` has a long built-in Markdown default.
NOT_IN_ENV_EXAMPLE = {"API_VERSION", "API_DESCRIPTION"}


def _env_var_names() -> list[str]:
    names = []
    for obj in vars(settings_module).values():
        if not (
            isinstance(obj, type) and issubclass(obj, BaseSettings) and obj is not BaseSettings
        ):
            continue
        if obj.__module__ != settings_module.__name__:
            continue
        prefix = obj.model_config.get("env_prefix") or ""
        # Aggregate classes (no own fields beyond sub-settings) contribute nothing.
        for field_name, field in obj.model_fields.items():
            if isinstance(field.annotation, type) and issubclass(field.annotation, BaseSettings):
                continue
            names.append(f"{prefix}{field_name}".upper())
    return sorted(set(names))


ENV_VARS = _env_var_names()


def test_settings_classes_were_discovered():
    assert len(ENV_VARS) >= 20, ENV_VARS


@pytest.mark.parametrize("name", ENV_VARS)
def test_env_var_documented_on_website(name):
    assert name in CONFIGURATION_DOC.read_text(encoding="utf-8"), (
        f"{name} is read by settings.py but missing from {CONFIGURATION_DOC.relative_to(REPO_ROOT)}"
    )


@pytest.mark.parametrize("name", [n for n in ENV_VARS if n not in NOT_IN_ENV_EXAMPLE])
def test_env_var_listed_in_env_example(name):
    assert name in ENV_EXAMPLE.read_text(encoding="utf-8"), (
        f"{name} is read by settings.py but missing from .env.example"
    )
