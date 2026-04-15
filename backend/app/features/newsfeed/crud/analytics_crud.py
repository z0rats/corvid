from collections import Counter, defaultdict
from datetime import datetime
from typing import Any
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.trends_blacklist_crud import get_blacklist_values
from app.features.newsfeed.models.newsfeed_models import NewsArticle
from app.features.newsfeed.utils.time_utils import parse_time_range

logger = logging.getLogger(__name__)

PARTITION_SIZE = 500


async def _query_articles_by_time(db: AsyncSession, columns: list, time_range: str | None):
    """Execute a select for the given columns, returning a Result for chunked iteration"""
    stmt = select(*columns)
    if time_range:
        cutoff = parse_time_range(time_range)
        if cutoff:
            stmt = stmt.where(NewsArticle.date >= cutoff)
    return await db.execute(stmt)


async def get_title_word_frequency(
    db: AsyncSession,
    limit: int = 20,
    time_range: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Analyze word frequency in article titles and return the top occurring words"""
    stmt = select(NewsArticle.id, NewsArticle.title, NewsArticle.date)

    if time_range:
        cutoff = parse_time_range(time_range)
        if cutoff:
            stmt = stmt.where(NewsArticle.date >= cutoff)
    else:
        if start_date:
            stmt = stmt.where(NewsArticle.date >= start_date)
        if end_date:
            stmt = stmt.where(NewsArticle.date <= end_date)

    result = await db.execute(stmt)

    stop_words = get_stop_words()
    blacklisted_words = await get_blacklist_values(db, "word")
    excluded_words = stop_words | blacklisted_words
    word_articles: dict[str, set] = {}
    word_counts: Counter = Counter()

    for partition in result.partitions(PARTITION_SIZE):
        for article in partition:
            for word in re.findall(r"\b[a-zA-Z]+\b", article.title.lower()):
                if word not in excluded_words and len(word) > 2:
                    word_articles.setdefault(word, set()).add(article.id)
                    word_counts[word] += 1

    return [
        {"word": word, "count": count, "article_ids": list(word_articles[word])}
        for word, count in word_counts.most_common(limit)
    ]


def get_stop_words() -> set:
    """Return the set of common stop words filtered from word frequency analysis"""
    return {
        "the", "and", "for", "with", "from", "that", "this", "have", "been", "has", "are",
        "was", "not", "but", "all", "its", "new", "more", "also", "into", "they", "their",
        "which", "could", "would", "should", "can", "will", "a", "an", "is", "of", "to", "in",
        "on", "at", "by", "be", "as", "or", "from", "it", "he", "she", "we", "you", "my",
        "your", "our", "us", "him", "her", "them", "his", "her", "its", "up", "down", "out",
        "about", "then", "there", "when", "where", "why", "how", "what", "who", "whom",
        "whose", "if", "than", "through", "before", "after", "while", "though", "even",
        "because", "until", "unless", "since", "about", "above", "across", "after", "against",
        "along", "among", "around", "at", "before", "behind", "below", "beneath", "beside",
        "between", "beyond", "but", "by", "concerning", "considering", "despite", "down",
        "during", "except", "for", "from", "in", "inside", "into", "like", "near", "of",
        "off", "on", "onto", "out", "outside", "over", "past", "regarding", "respecting",
        "round", "save", "since", "through", "throughout", "to", "toward", "towards", "under",
        "underneath", "until", "unto", "up", "upon", "with", "within", "without", "via", "re",
        "hackers", "cyber", "attack", "attacks", "data", "security", "says", "cybersecurity",
        "cve", "threat", "unveils", "group", "spread", "globe", "threats", "four",
    }


_IOC_KEY_MAP = {
    "md5_hashes": "md5",
    "sha1_hashes": "sha1",
    "sha256_hashes": "sha256",
}


async def get_top_iocs(db: AsyncSession, ioc_type: str, limit: int = 10, time_range: str | None = None) -> list[dict[str, Any]]:
    """Retrieve the most frequent IOCs of a specific type from the iocs JSON column"""
    db_key = _IOC_KEY_MAP.get(ioc_type, ioc_type)
    result = await _query_articles_by_time(db, [NewsArticle.id, NewsArticle.date, NewsArticle.iocs], time_range)
    blacklisted_iocs = await get_blacklist_values(db, "ioc")

    ioc_articles: dict[str, set] = defaultdict(set)
    ioc_counts: Counter = Counter()

    for partition in result.partitions(PARTITION_SIZE):
        for article in partition:
            iocs_data: dict | None = article.iocs
            if not iocs_data or db_key not in iocs_data or not isinstance(iocs_data[db_key], list):
                continue
            for value in iocs_data[db_key]:
                if isinstance(value, str) and value.strip() and value.strip().lower() not in blacklisted_iocs:
                    ioc_articles[value].add(article.id)
                    ioc_counts[value] += 1

    return [
        {"value": v, "count": c, "article_ids": list(ioc_articles[v])}
        for v, c in ioc_counts.most_common(limit)
    ]


async def get_top_cves(db: AsyncSession, limit: int = 10, time_range: str | None = None) -> list[dict[str, Any]]:
    """Retrieve the most frequent CVEs from the iocs JSON column"""
    result = await _query_articles_by_time(db, [NewsArticle.id, NewsArticle.date, NewsArticle.iocs], time_range)

    cve_articles: dict[str, set] = defaultdict(set)
    cve_counts: Counter = Counter()

    for partition in result.partitions(PARTITION_SIZE):
        for article in partition:
            iocs_data: dict | None = article.iocs
            if not iocs_data or "cves" not in iocs_data or not isinstance(iocs_data["cves"], list):
                continue
            for value in iocs_data["cves"]:
                if isinstance(value, str) and value.strip():
                    cve_articles[value].add(article.id)
                    cve_counts[value] += 1

    return [
        {"value": v, "count": c, "article_ids": list(cve_articles[v])}
        for v, c in cve_counts.most_common(limit)
    ]


async def get_ioc_type_distribution(db: AsyncSession, time_range: str | None = None) -> list[dict[str, Any]]:
    """Retrieve the total count of each IOC type within a specified time range"""
    result = await _query_articles_by_time(db, [NewsArticle.id, NewsArticle.date, NewsArticle.iocs], time_range)

    valid_ioc_types = ["ips", "md5", "sha1", "sha256", "urls", "domains", "emails", "cves"]
    ioc_type_counts: Counter = Counter()

    for partition in result.partitions(PARTITION_SIZE):
        for article in partition:
            iocs_data: dict | None = article.iocs
            if not iocs_data:
                continue
            for ioc_type in valid_ioc_types:
                if ioc_type in iocs_data and isinstance(iocs_data[ioc_type], list):
                    ioc_type_counts[ioc_type] += len(iocs_data[ioc_type])

    result_list = [
        {"id": ioc_type, "label": ioc_type.replace("_", " ").title(), "value": count}
        for ioc_type, count in ioc_type_counts.items()
    ]
    result_list.sort(key=lambda x: x["value"], reverse=True)
    return result_list
