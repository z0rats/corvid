"""Guards the seed content in default_template_data.py against schema drift -
e.g. a prompt edit that quietly exceeds AITemplateBase's length limits would
only otherwise surface at first-run seeding time in a fresh install."""

from app.features.llm_templates.schemas.llm_template_schemas import AITemplateCreate
from app.features.llm_templates.utils.default_template_data import DEFAULT_TEMPLATES


def test_every_default_template_validates_against_the_create_schema():
    for template_data in DEFAULT_TEMPLATES:
        AITemplateCreate(**{**template_data, "category_id": "dummy-category-id"})


def test_default_template_titles_are_unique():
    titles = [t["title"] for t in DEFAULT_TEMPLATES]
    assert len(titles) == len(set(titles))
