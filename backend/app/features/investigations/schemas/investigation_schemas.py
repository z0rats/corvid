import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


class InvestigationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Investigation name")
    notes: str | None = Field(default=None, max_length=20000, description="Analyst notes")

    _strip_name = field_validator("name")(_strip_required)


class InvestigationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        return None if value is None else _strip_required(value)


class ItemCreate(BaseModel):
    feature: str = Field(..., max_length=50, description="Feature name, e.g. 'ioc_lookup'")
    run_id: int = Field(..., ge=1, description="Run id within that feature's history")
    note: str | None = Field(default=None, max_length=5000)


class ItemUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=5000)


class InvestigationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    item_count: int = Field(..., description="Number of runs in the investigation")
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feature: str
    run_id: int
    target: str
    note: str | None
    added_at: datetime.datetime
    missing: bool = Field(
        default=False, description="The run was deleted from its feature's history"
    )


class InvestigationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    notes: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: list[ItemSchema] = Field(default_factory=list)


class SupportedFeature(BaseModel):
    feature: str
    label: str


class GraphRunRef(BaseModel):
    feature: str
    run_id: int


class GraphNodeSchema(BaseModel):
    id: str = Field(..., description="'<type>:<normalized value>'")
    type: str
    value: str
    raw_value: str = Field(..., description="The value as the source gave it, not normalized")
    label: str
    degree: int
    is_root: bool = Field(..., description="A run in the investigation was about this entity")
    sources: list[GraphRunRef]


class GraphEdgeSchema(BaseModel):
    source: str
    target: str
    relation: str
    sources: list[GraphRunRef]


class GraphResponse(BaseModel):
    nodes: list[GraphNodeSchema]
    edges: list[GraphEdgeSchema]
    total_nodes: int = Field(..., description="Nodes after the type filter, before the cap")
    truncated: bool = Field(..., description="Only the most connected nodes are returned")
    entity_types: list[str] = Field(..., description="Every entity type the API can return")
    type_counts: dict[str, int] = Field(
        ..., description="Entities per type before the type filter and the cap"
    )
