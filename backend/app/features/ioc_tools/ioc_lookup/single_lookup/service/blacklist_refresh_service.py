import asyncio
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import httpx
from lxml import etree
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ioc_tools.ioc_lookup.single_lookup.models.blacklist_models import (
    BlacklistedAddress, BlacklistSource,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import get_client
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import normalize_address

logger = logging.getLogger(__name__)

OFAC_SDN_URL = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"
SCAMSNIFFER_ADDRESS_URL = "https://raw.githubusercontent.com/scamsniffer/scam-database/main/blacklist/address.json"
SCAMSNIFFER_COMBINED_URL = "https://raw.githubusercontent.com/scamsniffer/scam-database/main/blacklist/combined.json"

# The SDN export is a multi-MB file fetched via a redirect to a presigned S3 URL; the
# shared client's default connect timeout (tuned for small, fast IOC-lookup calls) is too
# tight for this larger, redirecting download.
OFAC_FETCH_TIMEOUT = httpx.Timeout(connect=15.0, read=60.0, write=10.0, pool=10.0)

DIGITAL_CURRENCY_PREFIX = "Digital Currency Address - "
# OFAC uses the ISO 4217-style ticker "XBT" for Bitcoin; normalize to the common "BTC" code.
CHAIN_CODE_MAP = {"XBT": "BTC"}


def _local(elem: etree._Element) -> str:
    """Return the local (namespace-stripped) tag name of an lxml element."""
    return etree.QName(elem).localname


def _entity_name(sdn_entry: etree._Element) -> str | None:
    first = last = None
    for child in sdn_entry:
        local = _local(child)
        if local == "firstName":
            first = child.text
        elif local == "lastName":
            last = child.text
    parts = [p for p in (first, last) if p]
    return " ".join(parts) if parts else None


def _extract_digital_currency_entries(sdn_entry: etree._Element) -> list[dict[str, Any]]:
    """Extract Digital Currency Address id entries from a single sdnEntry element."""
    entity_name = _entity_name(sdn_entry)
    programs = [p.text for p in sdn_entry.iter() if _local(p) == "program" and p.text]
    remarks_el = next((e for e in sdn_entry.iter() if _local(e) == "remarks"), None)
    remarks = remarks_el.text if remarks_el is not None else None

    entries: list[dict[str, Any]] = []
    for id_el in sdn_entry.iter():
        if _local(id_el) != "id":
            continue
        id_type_el = next((c for c in id_el if _local(c) == "idType"), None)
        id_number_el = next((c for c in id_el if _local(c) == "idNumber"), None)
        if id_type_el is None or id_number_el is None or not id_type_el.text:
            continue
        if not id_type_el.text.startswith(DIGITAL_CURRENCY_PREFIX):
            continue

        chain_code = id_type_el.text[len(DIGITAL_CURRENCY_PREFIX):].strip()
        chain = CHAIN_CODE_MAP.get(chain_code, chain_code)
        address = (id_number_el.text or "").strip()
        if not address:
            continue

        details = {}
        if remarks:
            details["remarks"] = remarks
        if programs:
            details["programs"] = programs

        entries.append({
            "address": normalize_address(address),
            "chain": chain,
            "entity_name": entity_name,
            "label": ", ".join(programs) if programs else None,
            "details": details or None,
        })
    return entries


async def fetch_ofac_addresses() -> list[dict[str, Any]]:
    """Download and parse the OFAC SDN list, extracting Digital Currency Address entries.

    Streams the (multi-MB) XML with iterparse rather than loading a full DOM, clearing
    each sdnEntry after processing to bound memory use. This is a once-daily background
    job, not a hot path, so a full pass over the list is acceptable.
    """
    client = get_client()
    response = await client.get(OFAC_SDN_URL, follow_redirects=True, timeout=OFAC_FETCH_TIMEOUT)
    response.raise_for_status()

    results: list[dict[str, Any]] = []
    context = etree.iterparse(BytesIO(response.content), events=("end",))
    for _, elem in context:
        if _local(elem) != "sdnEntry":
            continue
        try:
            results.extend(_extract_digital_currency_entries(elem))
        finally:
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    logger.info("Parsed %d digital currency address entries from OFAC SDN list", len(results))
    return results


async def fetch_scamsniffer_addresses() -> list[dict[str, Any]]:
    """Download ScamSniffer's open EVM phishing-address blacklist (GPL-3.0, daily-updated)."""
    client = get_client()
    address_resp, combined_resp = await asyncio.gather(
        client.get(SCAMSNIFFER_ADDRESS_URL),
        client.get(SCAMSNIFFER_COMBINED_URL),
    )
    address_resp.raise_for_status()
    addresses: list[str] = address_resp.json()

    domain_by_address: dict[str, str] = {}
    if combined_resp.status_code == 200:
        try:
            combined: dict[str, list[str]] = combined_resp.json()
            for domain, addrs in combined.items():
                for addr in addrs:
                    domain_by_address.setdefault(normalize_address(addr), domain)
        except ValueError:
            logger.warning("Could not parse ScamSniffer combined.json; phishing-domain context will be missing")

    entries: list[dict[str, Any]] = []
    for raw_address in addresses:
        if not raw_address or not raw_address.strip():
            continue
        address = normalize_address(raw_address)
        phishing_domain = domain_by_address.get(address)
        entries.append({
            "address": address,
            "chain": "ETH",
            "entity_name": None,
            "label": "phishing",
            "details": {"phishing_domain": phishing_domain} if phishing_domain else None,
        })

    logger.info("Fetched %d phishing address entries from ScamSniffer", len(entries))
    return entries


async def _upsert_source_entries(db: AsyncSession, source: str, entries: list[dict[str, Any]]) -> None:
    """Soft-delete all rows for this source, then upsert every entry seen in this pass."""
    await db.execute(
        update(BlacklistedAddress).where(BlacklistedAddress.source == source).values(is_active=False)
    )

    seen_addresses: set[str] = set()
    for entry in entries:
        address = entry["address"]
        if not address or address in seen_addresses:
            continue
        seen_addresses.add(address)

        existing = (await db.execute(
            select(BlacklistedAddress).where(
                BlacklistedAddress.address == address, BlacklistedAddress.source == source
            )
        )).scalar_one_or_none()

        if existing:
            existing.chain = entry.get("chain")
            existing.label = entry.get("label")
            existing.entity_name = entry.get("entity_name")
            existing.details = entry.get("details")
            existing.is_active = True
            existing.last_seen_at = datetime.now(timezone.utc)
        else:
            db.add(BlacklistedAddress(
                address=address,
                source=source,
                chain=entry.get("chain"),
                label=entry.get("label"),
                entity_name=entry.get("entity_name"),
                details=entry.get("details"),
                is_active=True,
            ))

    await db.flush()


async def refresh_blacklist(db: AsyncSession) -> dict[str, int]:
    """Fetch both open data sources and refresh the local blacklist table.

    A failure in one source does not block the other; failed sources are
    reported with a count of -1 in the returned summary.
    """
    ofac_result, scamsniffer_result = await asyncio.gather(
        fetch_ofac_addresses(), fetch_scamsniffer_addresses(), return_exceptions=True,
    )

    summary: dict[str, int] = {}
    for source, result in (
        (BlacklistSource.OFAC.value, ofac_result),
        (BlacklistSource.SCAMSNIFFER.value, scamsniffer_result),
    ):
        if isinstance(result, Exception):
            logger.error("Failed to fetch %s blacklist data: %s", source, result)
            summary[source] = -1
            continue
        await _upsert_source_entries(db, source, result)
        summary[source] = len(result)

    logger.info("Blacklist refresh complete: %s", summary)
    return summary


async def is_blacklist_empty(db: AsyncSession) -> bool:
    """Check whether the blacklist table has any rows (used to trigger a first-run populate)."""
    result = await db.execute(select(BlacklistedAddress.id).limit(1))
    return result.first() is None
