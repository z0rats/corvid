import asyncio

import pytest

from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID
from app.features.llm_templates.crud.llm_template_crud import (
    create_new_template,
    delete_template_by_id,
    get_template_by_id,
    get_templates_with_pagination,
    move_templates_to_category,
    reorder_templates_by_ids,
    update_existing_template,
)
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.llm_templates.schemas.llm_template_schemas import (
    AITemplateCreate,
    AITemplateUpdate,
)


def _run(coro):
    return asyncio.run(coro)


def _create_request(**overrides):
    defaults = {
        "title": "Test Template",
        "ai_agent_role": "role",
        "ai_agent_task": "task",
    }
    return AITemplateCreate(**{**defaults, **overrides})


@pytest.fixture
def session_factory(make_session_factory):
    # AITemplate.category_id has a foreign key to template_categories, so both
    # tables must exist for create_all to resolve it.
    return make_session_factory([TemplateCategory.__table__, AITemplate.__table__])


class TestCreateNewTemplate:
    def test_defaults_category_id_when_none_given(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                template = await create_new_template(db, _create_request())
                await db.commit()
                return template

        template = _run(_scenario())
        assert template.category_id == DEFAULT_CATEGORY_ID

    def test_keeps_an_explicitly_given_category_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await create_new_template(
                    db, _create_request(category_id="some-other-category")
                )

        template = _run(_scenario())
        assert template.category_id == "some-other-category"


class TestGetTemplateById:
    def test_returns_none_when_no_row_exists(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_template_by_id(db, "does-not-exist")

        assert _run(_scenario()) is None

    def test_returns_the_matching_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_new_template(db, _create_request(title="Findable"))
                await db.commit()
                created_id = created.id

            async with session_factory() as db:
                return await get_template_by_id(db, created_id)

        found = _run(_scenario())
        assert found is not None
        assert found.title == "Findable"


class TestGetTemplatesWithPagination:
    def test_orders_by_order_number_ascending(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_template(db, _create_request(title="Second", order_number=20))
                await create_new_template(db, _create_request(title="First", order_number=10))
                await db.commit()

            async with session_factory() as db:
                return await get_templates_with_pagination(db)

        templates = _run(_scenario())
        assert [t.title for t in templates] == ["First", "Second"]

    def test_respects_skip_and_limit(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for i in range(5):
                    await create_new_template(db, _create_request(title=f"T{i}", order_number=i))
                await db.commit()

            async with session_factory() as db:
                return await get_templates_with_pagination(db, skip=2, limit=2)

        templates = _run(_scenario())
        assert [t.title for t in templates] == ["T2", "T3"]


class TestUpdateExistingTemplate:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await update_existing_template(
                    db, "does-not-exist", AITemplateUpdate(title="new")
                )

        assert _run(_scenario()) is None

    def test_updates_only_the_fields_that_were_set(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_new_template(
                    db, _create_request(title="Original", ai_agent_role="original role")
                )
                await db.commit()
                template_id = created.id

            async with session_factory() as db:
                return await update_existing_template(
                    db, template_id, AITemplateUpdate(title="Updated")
                )

        updated = _run(_scenario())
        assert updated.title == "Updated"
        assert updated.ai_agent_role == "original role"  # untouched


class TestDeleteTemplateById:
    def test_returns_false_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_template_by_id(db, "does-not-exist")

        assert _run(_scenario()) is False

    def test_deletes_the_row_and_returns_true(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_new_template(db, _create_request())
                await db.commit()
                template_id = created.id

            async with session_factory() as db:
                deleted = await delete_template_by_id(db, template_id)
                await db.commit()

            async with session_factory() as db:
                still_there = await get_template_by_id(db, template_id)
                return deleted, still_there

        deleted, still_there = _run(_scenario())
        assert deleted is True
        assert still_there is None


class TestReorderTemplatesByIds:
    def test_assigns_increasing_order_numbers_in_the_given_id_order(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                a = await create_new_template(db, _create_request(title="A"))
                b = await create_new_template(db, _create_request(title="B"))
                await db.commit()
                a_id, b_id = a.id, b.id

            async with session_factory() as db:
                # b listed first -> b gets the lower order number, regardless of
                # insertion order.
                return await reorder_templates_by_ids(
                    db, [b_id, a_id], start_order=10, increment=10
                )

        reordered = self._run_and_return_by_title(_scenario)
        assert reordered["B"] == 10
        assert reordered["A"] == 20

    @staticmethod
    def _run_and_return_by_title(scenario):
        templates = _run(scenario())
        return {t.title: t.order_number for t in templates}

    def test_silently_skips_unknown_ids(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_new_template(db, _create_request())
                await db.commit()
                template_id = created.id

            async with session_factory() as db:
                return await reorder_templates_by_ids(db, [template_id, "unknown-id"])

        reordered = _run(_scenario())
        assert len(reordered) == 1


class TestMoveTemplatesToCategory:
    def test_moves_the_given_templates_and_returns_the_count(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                a = await create_new_template(db, _create_request(title="A"))
                b = await create_new_template(db, _create_request(title="B"))
                await db.commit()
                a_id, b_id = a.id, b.id

            async with session_factory() as db:
                count = await move_templates_to_category(db, [a_id, b_id], "new-category")
                await db.commit()

            async with session_factory() as db:
                moved = await get_template_by_id(db, a_id)
                return count, moved.category_id

        count, category_id = _run(_scenario())
        assert count == 2
        assert category_id == "new-category"
