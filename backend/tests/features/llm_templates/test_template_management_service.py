import asyncio
from types import SimpleNamespace

import pytest

from app.features.llm_templates.schemas.llm_template_schemas import AITemplateExecute
from app.features.llm_templates.service import template_management_service as svc


def _run(coro):
    return asyncio.run(coro)


class TestParseJsonField:
    def test_parses_a_json_string_into_a_list(self):
        assert svc.parse_json_field('[{"a": 1}]', "payload_fields") == [{"a": 1}]

    def test_an_already_parsed_list_passes_through(self):
        assert svc.parse_json_field([{"a": 1}], "payload_fields") == [{"a": 1}]

    def test_none_becomes_an_empty_list(self):
        assert svc.parse_json_field(None, "payload_fields") == []

    def test_malformed_json_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            svc.parse_json_field("{not valid", "payload_fields")


class TestValidateRequiredPayloadFields:
    def test_passes_when_all_required_fields_are_provided(self):
        svc.validate_required_payload_fields(
            [{"name": "a", "required": True}, {"name": "b", "required": False}],
            {"a": "value"},
        )  # does not raise

    def test_raises_naming_the_missing_fields(self):
        with pytest.raises(ValueError, match="a"):
            svc.validate_required_payload_fields([{"name": "a", "required": True}], {})


class TestBuildTemplatePrompt:
    def test_substitutes_a_matching_tag_in_the_task_text(self):
        template = SimpleNamespace(ai_agent_task="Analyze this: <logs></logs>")

        prompt = svc.build_template_prompt(template, {"logs": "log line 1"})

        assert prompt == "Analyze this: log line 1"

    def test_appends_a_field_with_no_matching_tag_as_a_new_block(self):
        template = SimpleNamespace(ai_agent_task="Analyze this.")

        prompt = svc.build_template_prompt(template, {"logs": "log line 1"})

        assert "Analyze this." in prompt
        assert "<logs>\nlog line 1\n</logs>" in prompt

    def test_appends_static_and_web_context_sections_when_given(self):
        template = SimpleNamespace(ai_agent_task="Task")

        prompt = svc.build_template_prompt(
            template, {}, web_content="web stuff", static_content="static stuff"
        )

        assert "# Static Context" in prompt
        assert "static stuff" in prompt
        assert "# Web Context" in prompt
        assert "web stuff" in prompt


class TestFormatStaticContexts:
    def test_returns_an_empty_string_for_no_contexts(self):
        assert svc.format_static_contexts([]) == ""

    def test_joins_multiple_contexts_with_a_separator(self):
        result = svc.format_static_contexts(
            [
                {"name": "Ctx A", "content": "content A"},
                {"name": "Ctx B", "content": "content B", "description": "desc B"},
            ]
        )

        assert "## Ctx A" in result
        assert "content A" in result
        assert "## Ctx B" in result
        assert "desc B" in result
        assert "---" in result


class TestProcessWebContexts:
    def test_returns_an_empty_string_for_no_contexts(self):
        assert _run(svc.process_web_contexts([])) == ""

    def test_fetches_and_formats_web_contexts(self, monkeypatch):
        async def fake_fetch(web_contexts):
            return [
                {"name": "Page", "url": "https://example.com", "success": True, "content": "body"}
            ]

        monkeypatch.setattr(svc, "fetch_web_contexts", fake_fetch)

        result = _run(svc.process_web_contexts([{"name": "Page", "url": "https://example.com"}]))

        assert "## Page" in result
        assert "body" in result

    def test_degrades_to_a_warning_comment_when_fetching_fails(self, monkeypatch):
        async def failing_fetch(web_contexts):
            raise RuntimeError("network down")

        monkeypatch.setattr(svc, "fetch_web_contexts", failing_fetch)

        result = _run(svc.process_web_contexts([{"name": "Page", "url": "https://example.com"}]))

        assert "Warning: Failed to fetch web contexts" in result


class TestPrepareTemplateExecutionData:
    def test_uses_the_override_temperature_when_given(self):
        template = SimpleNamespace(
            payload_fields=[], web_contexts=[], static_contexts=[], model="gpt-4o", temperature=0.7
        )
        execution_data = AITemplateExecute(
            template_id="t1", payload_data={}, override_temperature=0.2
        )

        config = svc.prepare_template_execution_data(template, execution_data)

        assert config["temperature"] == 0.2
        assert config["model_id"] == "gpt-4o"

    def test_falls_back_to_the_template_temperature_when_no_override_given(self):
        template = SimpleNamespace(
            payload_fields=[], web_contexts=[], static_contexts=[], model=None, temperature=0.9
        )
        execution_data = AITemplateExecute(template_id="t1", payload_data={})

        config = svc.prepare_template_execution_data(template, execution_data)

        assert config["temperature"] == 0.9
        assert config["model_id"] == ""

    def test_override_model_takes_priority_over_the_template_model(self):
        template = SimpleNamespace(
            payload_fields=[],
            web_contexts=[],
            static_contexts=[],
            model="template-model",
            temperature=0.7,
        )
        execution_data = AITemplateExecute(
            template_id="t1", payload_data={}, override_model="override-model"
        )

        config = svc.prepare_template_execution_data(template, execution_data)

        assert config["model_id"] == "override-model"

    def test_raises_when_a_required_payload_field_is_missing(self):
        template = SimpleNamespace(
            payload_fields=[{"name": "logs", "required": True}],
            web_contexts=[],
            static_contexts=[],
            model=None,
            temperature=0.7,
        )
        execution_data = AITemplateExecute(template_id="t1", payload_data={})

        with pytest.raises(ValueError, match="logs"):
            svc.prepare_template_execution_data(template, execution_data)


class TestRunEngineerPrompt:
    def test_uses_the_configured_default_model_when_the_requested_one_is_unavailable(
        self, monkeypatch
    ):
        calls = {}

        async def fake_build_model_registry(db):
            return {"gpt-4o": object()}

        async def fake_get_default_model_id(db, module_key):
            calls["default_lookup"] = module_key
            return "gpt-4o"

        async def fake_execute_structured_prompt(models, *, model_id, **kwargs):
            calls["model_id"] = model_id
            return SimpleNamespace(
                model_dump=lambda: {
                    "ai_agent_role": "role",
                    "ai_agent_task": "task",
                    "payload_fields": [],
                    "example_input_output": "example",
                }
            )

        monkeypatch.setattr(svc, "build_model_registry", fake_build_model_registry)
        monkeypatch.setattr(svc, "get_default_model_id", fake_get_default_model_id)
        monkeypatch.setattr(svc, "execute_structured_prompt", fake_execute_structured_prompt)

        result = _run(svc.run_engineer_prompt("Title", "Description", "not-available", db=None))

        assert calls["default_lookup"] == "llm_templates"
        assert calls["model_id"] == "gpt-4o"
        assert result["ai_agent_role"] == "role"


class TestRunExecuteTemplate:
    def test_falls_back_to_the_default_model_when_the_templates_model_is_unavailable(
        self, monkeypatch
    ):
        calls = {}

        template = SimpleNamespace(
            payload_fields=[],
            web_contexts=[],
            static_contexts=[],
            model="unavailable-model",
            temperature=0.7,
            ai_agent_task="Task",
            ai_agent_role="Role",
        )
        execution_data = AITemplateExecute(template_id="t1", payload_data={})

        async def fake_build_model_registry(db):
            return {"gpt-4o": object()}

        async def fake_get_default_model_id(db, module_key):
            return "gpt-4o"

        async def fake_execute_prompt(models, *, model_id, **kwargs):
            calls["model_id"] = model_id
            return "the llm result"

        monkeypatch.setattr(svc, "build_model_registry", fake_build_model_registry)
        monkeypatch.setattr(svc, "get_default_model_id", fake_get_default_model_id)
        monkeypatch.setattr(svc, "execute_prompt", fake_execute_prompt)

        result = _run(svc.run_execute_template(template, execution_data, db=None))

        assert calls["model_id"] == "gpt-4o"
        assert result == "the llm result"
