import asyncio

import pytest

from app.features.llm_templates.constants import DEFAULT_CATEGORY_ID, FAVORITES_CATEGORY_ID
from app.features.llm_templates.crud.llm_template_crud import (
    create_new_template,
    get_template_by_id,
)
from app.features.llm_templates.crud.template_category_crud import (
    create_category,
    delete_category,
    ensure_system_categories_exist,
    get_all_categories,
    get_category_by_id,
    reorder_categories,
    update_category_name,
)
from app.features.llm_templates.models.llm_template_models import AITemplate
from app.features.llm_templates.models.template_category_models import TemplateCategory
from app.features.llm_templates.schemas.llm_template_schemas import AITemplateCreate


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([TemplateCategory.__table__, AITemplate.__table__])


class TestCreateCategory:
    def test_assigns_the_next_order_number_after_the_current_max(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_category(db, "First")
                await db.commit()
                second = await create_category(db, "Second")
                return second.order_number

        assert _run(_scenario()) == 20  # first gets 10, second gets max(10) + 10

    def test_first_category_starts_at_ten(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                category = await create_category(db, "First")
                return category.order_number

        assert _run(_scenario()) == 10


class TestGetCategoryById:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_category_by_id(db, "does-not-exist")

        assert _run(_scenario()) is None


class TestGetAllCategories:
    def test_orders_by_order_number_ascending(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_category(db, "A")  # order 10
                await create_category(db, "B")  # order 20
                await db.commit()
                return await get_all_categories(db)

        categories = _run(_scenario())
        assert [c.name for c in categories] == ["A", "B"]


class TestUpdateCategoryName:
    def test_returns_none_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await update_category_name(db, "does-not-exist", "new name")

        assert _run(_scenario()) is None

    def test_renames_a_non_system_category(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                category = await create_category(db, "Old Name")
                await db.commit()
                category_id = category.id

            async with session_factory() as db:
                return await update_category_name(db, category_id, "New Name")

        renamed = _run(_scenario())
        assert renamed.name == "New Name"

    def test_raises_for_a_system_category(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                await db.commit()

            async with session_factory() as db:
                await update_category_name(db, DEFAULT_CATEGORY_ID, "Renamed Default")

        with pytest.raises(ValueError, match="cannot be renamed"):
            _run(_scenario())


class TestDeleteCategory:
    def test_returns_false_for_an_unknown_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_category(db, "does-not-exist", "move_to_default")

        assert _run(_scenario()) is False

    def test_raises_for_a_system_category(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                await db.commit()

            async with session_factory() as db:
                await delete_category(db, FAVORITES_CATEGORY_ID, "move_to_default")

        with pytest.raises(ValueError, match="cannot be deleted"):
            _run(_scenario())

    def test_move_to_default_reassigns_templates_before_deleting_the_category(
        self, session_factory
    ):
        async def _scenario():
            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                category = await create_category(db, "To Delete")
                await db.commit()
                category_id = category.id

            async with session_factory() as db:
                template = await create_new_template(
                    db,
                    AITemplateCreate(
                        title="t", ai_agent_role="r", ai_agent_task="k", category_id=category_id
                    ),
                )
                await db.commit()
                template_id = template.id

            async with session_factory() as db:
                deleted = await delete_category(db, category_id, "move_to_default")
                await db.commit()

            async with session_factory() as db:
                template = await get_template_by_id(db, template_id)
                category = await get_category_by_id(db, category_id)
                return deleted, template.category_id, category

        deleted, moved_category_id, remaining_category = _run(_scenario())
        assert deleted is True
        assert moved_category_id == DEFAULT_CATEGORY_ID
        assert remaining_category is None

    def test_delete_templates_removes_the_templates_along_with_the_category(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                category = await create_category(db, "To Delete")
                await db.commit()
                category_id = category.id

            async with session_factory() as db:
                template = await create_new_template(
                    db,
                    AITemplateCreate(
                        title="t", ai_agent_role="r", ai_agent_task="k", category_id=category_id
                    ),
                )
                await db.commit()
                template_id = template.id

            async with session_factory() as db:
                await delete_category(db, category_id, "delete_templates")
                await db.commit()

            async with session_factory() as db:
                return await get_template_by_id(db, template_id)

        assert _run(_scenario()) is None


class TestReorderCategories:
    def test_assigns_increasing_order_numbers_in_the_given_id_order(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                a = await create_category(db, "A")
                b = await create_category(db, "B")
                await db.commit()
                a_id, b_id = a.id, b.id

            async with session_factory() as db:
                return await reorder_categories(db, [b_id, a_id], start_order=0, increment=10)

        reordered = _run(_scenario())
        by_name = {c.name: c.order_number for c in reordered}
        assert by_name == {"B": 0, "A": 10}


class TestEnsureSystemCategoriesExist:
    def test_creates_both_system_categories_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                await db.commit()
                return await get_all_categories(db)

        categories = _run(_scenario())
        ids = {c.id for c in categories}
        assert {FAVORITES_CATEGORY_ID, DEFAULT_CATEGORY_ID} <= ids
        assert all(c.is_system for c in categories)

    def test_is_idempotent_when_categories_already_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                await db.commit()

            async with session_factory() as db:
                await ensure_system_categories_exist(db)
                await db.commit()
                return await get_all_categories(db)

        categories = _run(_scenario())
        assert len(categories) == 2
