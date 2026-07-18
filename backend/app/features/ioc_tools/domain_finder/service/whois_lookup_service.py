"""
WHOIS/RDAP lookup business logic: fetches raw RDAP data and parses it into a
flat, UI-friendly shape (registrar, key dates, registrant org, nameservers).
"""
import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import AppHTTPException

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    WhoisEntity,
    WhoisLookupRequest,
    WhoisLookupResponse,
)
from app.features.ioc_tools.domain_finder.service.rdap_api_service import fetch_rdap_domain_data

logger = logging.getLogger(__name__)


async def perform_whois_lookup(whois_request: WhoisLookupRequest) -> WhoisLookupResponse:
    """
    Perform a WHOIS-style domain lookup via RDAP.

    Args:
        whois_request: Validated WHOIS lookup request containing the domain to look up

    Returns:
        WhoisLookupResponse containing parsed registration data plus the raw RDAP record

    Raises:
        AppHTTPException: When the RDAP request fails or the domain has no RDAP record
    """
    domain = whois_request.domain
    logger.info("Starting WHOIS/RDAP lookup for: %s", domain)

    raw, rdap_server = await fetch_rdap_domain_data(domain)

    entities = _extract_entities(raw)
    events = _extract_events(raw)
    registrar, registrar_iana_id = _extract_registrar(raw)
    registrant_org = next(
        (e.organization for e in entities if e.role == "registrant" and e.organization), None
    )

    response = WhoisLookupResponse(
        domain=domain,
        rdap_server=rdap_server,
        registrar=registrar,
        registrar_iana_id=registrar_iana_id,
        creation_date=_parse_rdap_date(events.get("registration")),
        expiration_date=_parse_rdap_date(events.get("expiration")),
        updated_date=_parse_rdap_date(events.get("last changed")),
        registrant_organization=registrant_org,
        statuses=raw.get("status") or [],
        nameservers=[
            ns.get("ldhName") for ns in (raw.get("nameservers") or []) if ns.get("ldhName")
        ],
        entities=entities,
        raw=raw,
    )

    logger.info("WHOIS/RDAP lookup completed for: %s via %s", domain, rdap_server)
    return response


def _parse_vcard(vcard_array: Any) -> dict[str, str]:
    """Parse an RDAP jCard/vCard array into a flat {name, organization, email} dict"""
    parsed: dict[str, str] = {}
    if not isinstance(vcard_array, list) or len(vcard_array) < 2:
        return parsed

    for entry in vcard_array[1]:
        if not isinstance(entry, list) or len(entry) < 4:
            continue
        prop, _params, _value_type, value = entry[0], entry[1], entry[2], entry[3]
        if prop == "fn" and value:
            parsed["name"] = value
        elif prop == "org" and value:
            parsed["organization"] = value[0] if isinstance(value, list) else value
        elif prop == "email" and value:
            parsed["email"] = value

    return parsed


def _extract_entities(raw: dict[str, Any], _entities: list[dict[str, Any]] | None = None) -> list[WhoisEntity]:
    """Flatten RDAP entities (including nested ones, e.g. an abuse contact under a registrar)"""
    entities: list[WhoisEntity] = []
    for entity in _entities if _entities is not None else (raw.get("entities") or []):
        roles = entity.get("roles") or ["unknown"]
        vcard = _parse_vcard(entity.get("vcardArray"))
        for role in roles:
            entities.append(WhoisEntity(
                role=role,
                name=vcard.get("name"),
                organization=vcard.get("organization"),
                email=vcard.get("email"),
            ))
        nested = entity.get("entities")
        if nested:
            entities.extend(_extract_entities(raw, nested))
    return entities


def _extract_events(raw: dict[str, Any]) -> dict[str, str]:
    """Map RDAP eventAction -> eventDate (ISO string)"""
    events: dict[str, str] = {}
    for event in raw.get("events") or []:
        action = event.get("eventAction")
        date_str = event.get("eventDate")
        if action and date_str:
            events[action] = date_str
    return events


def _extract_registrar(raw: dict[str, Any]) -> tuple[str | None, str | None]:
    """Find the registrar entity and return (name, IANA registrar ID)"""
    registrar_entity = next(
        (e for e in raw.get("entities") or [] if "registrar" in (e.get("roles") or [])), None
    )
    if not registrar_entity:
        return None, None

    vcard = _parse_vcard(registrar_entity.get("vcardArray"))
    name = vcard.get("organization") or vcard.get("name")

    iana_id = None
    for public_id in registrar_entity.get("publicIds") or []:
        if public_id.get("type") == "IANA Registrar ID":
            iana_id = public_id.get("identifier")
            break

    return name, iana_id


def _parse_rdap_date(date_str: str | None) -> datetime | None:
    """Parse an RDAP eventDate (ISO 8601, typically 'Z'-suffixed) into a datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Could not parse RDAP event date: %s", date_str)
        return None
