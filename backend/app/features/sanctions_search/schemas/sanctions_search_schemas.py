import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MatchedOn = Literal["exact_name", "exact_alias", "substring_name", "substring_alias"]


class SanctionsMatch(BaseModel):
    """One OpenSanctions/OFAC SDN entity matching the search query."""

    # `schema` is the wire/OpenSanctions field name (kept for API-contract clarity), but
    # BaseModel itself defines a `schema` classmethod - aliasing avoids the attribute clash
    # mypy catches on a plain same-named field. `populate_by_name` lets the service layer's
    # dicts (built with the literal "schema" key) validate either way.
    model_config = ConfigDict(populate_by_name=True)

    opensanctions_id: str
    entity_schema: str = Field(
        ..., alias="schema", description="Person, Organization, Vessel, Airplane, ..."
    )
    name: str
    aliases: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    programs: list[str] = Field(default_factory=list, description="Sanctions program ids")
    sanctions: str | None = Field(default=None, description="Free-text designation description")
    first_seen: datetime.date | None = None
    last_seen: datetime.date | None = None
    matched_on: MatchedOn = Field(..., description="Which ranked bucket this match came from")


class SanctionsSearchResponse(BaseModel):
    """Result of a free-text name/alias search against the locally cached OFAC SDN mirror."""

    query: str
    schema_filter: str | None = None
    as_of: str = Field(..., description="Date the local copy of the list was last refreshed")
    outdated: bool = Field(
        ..., description="Whether the local copy is older than the source's own update rhythm"
    )
    matches: list[SanctionsMatch] = Field(default_factory=list)
    total_matches: int = Field(..., ge=0, description="Matches found before truncation to `limit`")
    truncated: bool = Field(..., description="Whether total_matches exceeded the requested limit")
