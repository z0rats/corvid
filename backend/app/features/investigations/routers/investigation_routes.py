import logging
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Query, Response, status
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.entities.model import ENTITY_TYPES
from app.core.exceptions import AppHTTPException
from app.features.investigations.crud import investigation_crud as crud
from app.features.investigations.models.investigation_models import (
    Investigation,
    InvestigationItem,
)
from app.features.investigations.schemas.investigation_schemas import (
    GraphEdgeSchema,
    GraphNodeSchema,
    GraphResponse,
    GraphRunRef,
    InvestigationCreate,
    InvestigationDetail,
    InvestigationSummary,
    InvestigationUpdate,
    ItemCreate,
    ItemSchema,
    ItemUpdate,
    SupportedFeature,
)
from app.features.investigations.service.investigation_service import (
    build_graph,
    generate_investigation_report,
    missing_item_ids,
    resolve_items,
)
from app.utils.run_source_registry import RUN_SOURCES, get_run_source

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])


def _item_exists() -> AppHTTPException:
    return AppHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This run is already in the investigation",
        error_code="INVESTIGATION_ITEM_EXISTS",
    )


_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Investigation not found"}}


async def _get_or_404(db, investigation_id: int) -> Investigation:
    investigation = await crud.get_investigation(db, investigation_id)
    if investigation is None:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found",
            error_code="INVESTIGATION_NOT_FOUND",
        )
    return investigation


def _item_schema(item: InvestigationItem, missing: bool) -> ItemSchema:
    return ItemSchema.model_validate(item).model_copy(update={"missing": missing})


async def _detail(db, investigation: Investigation) -> InvestigationDetail:
    """Items with only their tombstone flag - never their runs' results, which a detail view
    (and every notes save) has no use for."""
    missing = await missing_item_ids(db, investigation.items)
    return InvestigationDetail(
        id=investigation.id,
        name=investigation.name,
        notes=investigation.notes,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        items=[_item_schema(item, item.id in missing) for item in investigation.items],
    )


def _summary(investigation: Investigation, item_count: int) -> InvestigationSummary:
    return InvestigationSummary(
        id=investigation.id,
        name=investigation.name,
        notes=investigation.notes,
        item_count=item_count,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
    )


@router.get(
    "/features",
    response_model=list[SupportedFeature],
    summary="Features that can be added",
    description="Features whose runs can be added to an investigation",
)
async def read_supported_features() -> list[SupportedFeature]:
    return [
        SupportedFeature(feature=key, label=source.label) for key, source in RUN_SOURCES.items()
    ]


@router.get(
    "/memberships",
    response_model=list[InvestigationSummary],
    summary="Investigations holding a run",
    description="Investigations that already contain the given run",
)
async def read_memberships(
    db: ReadSessionDep,
    feature: Annotated[str, Query(max_length=50)],
    run_id: Annotated[int, Query(ge=1)],
) -> list[InvestigationSummary]:
    return [_summary(inv, count) for inv, count in await crud.list_memberships(db, feature, run_id)]


@router.get(
    "",
    response_model=list[InvestigationSummary],
    summary="List investigations",
    description="Every investigation with its item count, most recently updated first",
)
async def read_investigations(db: ReadSessionDep) -> list[InvestigationSummary]:
    return [_summary(inv, count) for inv, count in await crud.list_investigations(db)]


@router.post(
    "",
    response_model=InvestigationDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create an investigation",
    description="Create an empty, named investigation",
)
async def create_investigation(db: SessionDep, body: InvestigationCreate) -> InvestigationDetail:
    investigation = await crud.create_investigation(db, body.name, body.notes)
    logger.info("Created investigation %s", investigation.id)
    return await _detail(db, await _get_or_404(db, investigation.id))


@router.get(
    "/{investigation_id}",
    response_model=InvestigationDetail,
    summary="Get an investigation",
    description="An investigation with its items; a run deleted from history is `missing`",
    responses=_NOT_FOUND,
)
async def read_investigation(investigation_id: int, db: ReadSessionDep) -> InvestigationDetail:
    return await _detail(db, await _get_or_404(db, investigation_id))


@router.patch(
    "/{investigation_id}",
    response_model=InvestigationDetail,
    summary="Rename an investigation or edit its notes",
    description="Update the name and/or notes; omitted fields are left as they are",
    responses=_NOT_FOUND,
)
async def update_investigation(
    investigation_id: int, db: SessionDep, body: InvestigationUpdate
) -> InvestigationDetail:
    investigation = await _get_or_404(db, investigation_id)
    fields = body.model_dump(exclude_unset=True)
    if fields.get("name") is not None:
        investigation.name = fields["name"]
    if "notes" in fields:
        investigation.notes = fields["notes"]
    crud.touch(investigation)
    await db.flush()
    return await _detail(db, investigation)


@router.delete(
    "/{investigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an investigation",
    description="Delete the investigation and its items; the referenced runs are not touched",
    responses=_NOT_FOUND,
)
async def delete_investigation(investigation_id: int, db: SessionDep) -> None:
    await crud.delete_investigation(db, await _get_or_404(db, investigation_id))
    logger.info("Deleted investigation %s", investigation_id)


@router.post(
    "/{investigation_id}/items",
    response_model=ItemSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add a run to an investigation",
    description="Reference an existing run of a supported feature",
    responses={
        **_NOT_FOUND,
        409: {"description": "Run already in this investigation"},
        422: {"description": "Feature not supported, or run not found"},
    },
)
async def add_item(investigation_id: int, db: SessionDep, body: ItemCreate) -> ItemSchema:
    investigation = await _get_or_404(db, investigation_id)
    source = get_run_source(body.feature)
    if source is None:
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Runs of '{body.feature}' can't be added to an investigation",
            error_code="INVESTIGATION_FEATURE_UNSUPPORTED",
        )
    # The run row alone: every source's target is a column of it, results aren't needed.
    model: Any = source.model
    run = await db.get(model, body.run_id)
    if run is None:
        raise AppHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Run not found",
            error_code="INVESTIGATION_RUN_NOT_FOUND",
        )
    if await crud.find_item(db, investigation.id, body.feature, body.run_id):
        raise _item_exists()
    try:
        item = await crud.add_item(
            db, investigation, body.feature, body.run_id, source.target(run), body.note
        )
    except IntegrityError:
        # A concurrent add of the same run (a double click) passed find_item too; the unique
        # constraint is what actually decides, so its violation is the same 409.
        raise _item_exists() from None
    return ItemSchema.model_validate(item)


async def _item_or_404(db, investigation_id: int, item_id: int):
    item = await crud.get_item(db, investigation_id, item_id)
    if item is None:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
            error_code="INVESTIGATION_ITEM_NOT_FOUND",
        )
    return item


@router.patch(
    "/{investigation_id}/items/{item_id}",
    response_model=ItemSchema,
    summary="Edit an item's note",
    description="Replace the analyst note on one item",
    responses={404: {"description": "Investigation or item not found"}},
)
async def update_item(
    investigation_id: int, item_id: int, db: SessionDep, body: ItemUpdate
) -> ItemSchema:
    investigation = await _get_or_404(db, investigation_id)
    item = await _item_or_404(db, investigation_id, item_id)
    item.note = body.note
    crud.touch(investigation)
    await db.flush()
    return _item_schema(item, item.id in await missing_item_ids(db, [item]))


@router.delete(
    "/{investigation_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a run from an investigation",
    description="Remove the reference; the run itself stays in its feature's history",
    responses={404: {"description": "Investigation or item not found"}},
)
async def delete_item(investigation_id: int, item_id: int, db: SessionDep) -> None:
    investigation = await _get_or_404(db, investigation_id)
    await crud.delete_item(db, investigation, await _item_or_404(db, investigation_id, item_id))


@router.get(
    "/{investigation_id}/report",
    summary="Export an investigation as a report",
    description="One HTML or PDF covering every item, plus the most connected entities",
    responses=_NOT_FOUND,
)
async def export_report(
    investigation_id: int,
    db: ReadSessionDep,
    format: Literal["html", "pdf"] = "html",
    locale: Literal["en", "ru"] = "en",
) -> Response:
    investigation = await _get_or_404(db, investigation_id)
    resolved = await resolve_items(db, investigation)
    content, media_type, filename = generate_investigation_report(
        investigation, resolved, format, locale
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{investigation_id}/graph",
    response_model=GraphResponse,
    summary="Entity graph of an investigation",
    description=(
        "Entities and links derived from the investigation's runs on every request. Past the "
        "node cap only the most connected nodes are returned and `truncated` is set"
    ),
    responses=_NOT_FOUND,
)
async def read_graph(
    investigation_id: int,
    db: ReadSessionDep,
    types: Annotated[
        list[str] | None, Query(description="Only these entity types (default: all)")
    ] = None,
) -> GraphResponse:
    investigation = await _get_or_404(db, investigation_id)
    graph = build_graph(await resolve_items(db, investigation), types)

    def refs(sources) -> list[GraphRunRef]:
        return [
            GraphRunRef(feature=ref.feature, run_id=ref.run_id)
            for ref in sorted(sources, key=lambda ref: (ref.feature, ref.run_id))
        ]

    return GraphResponse(
        nodes=[
            GraphNodeSchema(
                id=node.entity.id,
                type=node.entity.type,
                value=node.entity.value,
                raw_value=node.entity.raw or node.entity.value,
                label=node.entity.label,
                degree=node.degree,
                is_root=node.is_root,
                sources=refs(node.sources),
            )
            for node in graph.nodes.values()
        ],
        edges=[
            GraphEdgeSchema(
                source=edge.source,
                target=edge.target,
                relation=edge.relation,
                sources=refs(edge.sources),
            )
            for edge in graph.edges.values()
        ],
        total_nodes=graph.total_nodes,
        truncated=graph.truncated,
        entity_types=list(ENTITY_TYPES),
        type_counts=graph.type_counts,
    )
