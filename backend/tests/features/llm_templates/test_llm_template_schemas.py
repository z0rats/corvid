import datetime

import pytest
from pydantic import ValidationError

from app.features.llm_templates.schemas.llm_template_schemas import (
    AITemplate,
    AITemplateBase,
    AITemplateExecute,
    CategoryDeleteRequest,
    PayloadField,
    WebContext,
)


class TestPayloadField:
    def test_accepts_alphanumeric_hyphen_and_underscore_names(self):
        field = PayloadField(name="patch_notes-v2", description="desc")
        assert field.name == "patch_notes-v2"

    def test_rejects_a_name_with_invalid_characters(self):
        with pytest.raises(ValidationError, match="alphanumeric"):
            PayloadField(name="patch notes!", description="desc")


class TestWebContext:
    def test_accepts_an_http_or_https_url(self):
        assert WebContext(name="x", url="https://example.com").url == "https://example.com"

    def test_rejects_a_url_without_a_scheme(self):
        with pytest.raises(ValidationError, match="http"):
            WebContext(name="x", url="example.com/page")


class TestAITemplateBaseValidators:
    base_kwargs = {
        "title": "t",
        "ai_agent_role": "role",
        "ai_agent_task": "task",
    }

    def test_rejects_a_duplicate_payload_field_name(self):
        with pytest.raises(ValidationError, match="Duplicate payload field name"):
            AITemplateBase(
                **self.base_kwargs,
                payload_fields=[
                    {"name": "x", "description": "first"},
                    {"name": "x", "description": "second"},
                ],
            )

    def test_rejects_a_payload_field_missing_a_name(self):
        with pytest.raises(ValidationError, match="must have a name"):
            AITemplateBase(**self.base_kwargs, payload_fields=[{"description": "no name"}])

    def test_rejects_a_payload_field_that_is_not_a_dict(self):
        # Caught by pydantic's own `list[dict[str, Any]]` element typing before the
        # field_validator's own isinstance check ever runs.
        with pytest.raises(ValidationError, match="valid dictionary"):
            AITemplateBase(**self.base_kwargs, payload_fields=["not-a-dict"])

    def test_rejects_an_invalid_static_context(self):
        with pytest.raises(ValidationError, match="Invalid static context"):
            AITemplateBase(**self.base_kwargs, static_contexts=[{"name": "x"}])  # missing content

    def test_rejects_an_invalid_web_context_url(self):
        with pytest.raises(ValidationError, match="Invalid web context"):
            AITemplateBase(**self.base_kwargs, web_contexts=[{"name": "x", "url": "not-a-url"}])

    def test_blank_model_is_normalised_to_none(self):
        template = AITemplateBase(**self.base_kwargs, model="   ")
        assert template.model is None

    def test_non_blank_model_is_stripped(self):
        template = AITemplateBase(**self.base_kwargs, model="  gpt-4o  ")
        assert template.model == "gpt-4o"


class TestAITemplateResponseNormalisesDbJsonStrings:
    def _base_kwargs(self, **overrides):
        return {
            "id": "abc",
            "title": "t",
            "ai_agent_role": "role",
            "ai_agent_task": "task",
            "created_at": datetime.datetime.now(datetime.UTC),
            "updated_at": datetime.datetime.now(datetime.UTC),
            **overrides,
        }

    def test_parses_a_json_string_payload_fields_column_into_a_list(self):
        template = AITemplate(
            **self._base_kwargs(payload_fields='[{"name": "x", "description": "d"}]')
        )
        assert template.payload_fields == [{"name": "x", "description": "d"}]

    def test_malformed_json_string_degrades_to_an_empty_list_rather_than_raising(self):
        template = AITemplate(**self._base_kwargs(payload_fields="{not valid json"))
        assert template.payload_fields == []

    def test_an_already_parsed_list_passes_through_unchanged(self):
        template = AITemplate(**self._base_kwargs(static_contexts=[{"name": "x", "content": "y"}]))
        assert template.static_contexts == [{"name": "x", "content": "y"}]

    def test_none_becomes_an_empty_list(self):
        template = AITemplate(**self._base_kwargs(web_contexts=None))
        assert template.web_contexts == []


class TestAITemplateExecute:
    def test_rejects_a_blank_payload_data_key(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            AITemplateExecute(template_id="t1", payload_data={"  ": "value"})

    def test_strips_the_override_model(self):
        execute = AITemplateExecute(template_id="t1", payload_data={}, override_model="  gpt-4o  ")
        assert execute.override_model == "gpt-4o"

    def test_blank_override_model_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            AITemplateExecute(template_id="t1", payload_data={}, override_model="   ")


class TestCategoryDeleteRequest:
    def test_accepts_the_two_documented_actions(self):
        assert CategoryDeleteRequest(action="move_to_default").action == "move_to_default"
        assert CategoryDeleteRequest(action="delete_templates").action == "delete_templates"

    def test_rejects_any_other_action(self):
        with pytest.raises(ValidationError):
            CategoryDeleteRequest(action="delete_everything")
