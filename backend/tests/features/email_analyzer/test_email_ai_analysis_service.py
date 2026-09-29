import asyncio

from app.features.email_analyzer.service import email_ai_analysis_service as svc


def _run(coro):
    return asyncio.run(coro)


def _async_return(value):
    async def _inner(*args, **kwargs):
        return value

    return _inner


def _fail_if_called(name):
    async def _inner(*args, **kwargs):
        raise AssertionError(f"{name} should not have been called")

    return _inner


class TestAnalyzeEmailBody:
    def test_resolves_the_default_model_for_this_module_when_none_is_given(self, monkeypatch):
        calls = {}

        async def fake_get_default_model_id(db, module_key):
            calls["module_key"] = module_key
            return "resolved-model"

        async def fake_execute_prompt(models, *, model_id, **kwargs):
            calls["model_id"] = model_id
            return "the analysis"

        monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
        monkeypatch.setattr(svc, "get_default_model_id", fake_get_default_model_id)
        monkeypatch.setattr(svc, "execute_prompt", fake_execute_prompt)

        result = _run(svc.analyze_email_body("suspicious body", db=None))

        assert calls["module_key"] == "email_analyzer"
        assert calls["model_id"] == "resolved-model"
        assert result == "the analysis"

    def test_uses_the_given_model_id_without_resolving_a_default(self, monkeypatch):
        calls = {}

        async def fake_execute_prompt(models, *, model_id, **kwargs):
            calls["model_id"] = model_id
            return "the analysis"

        monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
        monkeypatch.setattr(svc, "get_default_model_id", _fail_if_called("get_default_model_id"))
        monkeypatch.setattr(svc, "execute_prompt", fake_execute_prompt)

        result = _run(svc.analyze_email_body("suspicious body", db=None, model_id="explicit-model"))

        assert calls["model_id"] == "explicit-model"
        assert result == "the analysis"

    def test_passes_the_system_prompt_and_embeds_the_email_body_in_the_user_prompt(
        self, monkeypatch
    ):
        calls = {}

        async def fake_execute_prompt(models, *, model_id, system_prompt, user_prompt, **kwargs):
            calls["system_prompt"] = system_prompt
            calls["user_prompt"] = user_prompt
            return "the analysis"

        monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
        monkeypatch.setattr(svc, "get_default_model_id", _async_return("resolved-model"))
        monkeypatch.setattr(svc, "execute_prompt", fake_execute_prompt)

        _run(svc.analyze_email_body("Click http://evil.example/login now!", db=None))

        assert calls["system_prompt"] == svc.SYSTEM_PROMPT
        assert "Click http://evil.example/login now!" in calls["user_prompt"]

    def test_passes_the_temperature_through_to_execute_prompt(self, monkeypatch):
        calls = {}

        async def fake_execute_prompt(models, *, model_id, temperature, **kwargs):
            calls["temperature"] = temperature
            return "the analysis"

        monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
        monkeypatch.setattr(svc, "get_default_model_id", _async_return("resolved-model"))
        monkeypatch.setattr(svc, "execute_prompt", fake_execute_prompt)

        _run(svc.analyze_email_body("body", db=None, temperature=0.2))

        assert calls["temperature"] == 0.2

    def test_returns_the_execute_prompt_result_unchanged(self, monkeypatch):
        monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
        monkeypatch.setattr(svc, "get_default_model_id", _async_return("resolved-model"))
        monkeypatch.setattr(
            svc, "execute_prompt", _async_return("## Overall Assessment\nSuspicious")
        )

        result = _run(svc.analyze_email_body("body", db=None))

        assert result == "## Overall Assessment\nSuspicious"
