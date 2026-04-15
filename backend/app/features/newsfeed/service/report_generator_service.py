import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.news_articles_crud import (
    get_recent_news_articles,
    get_news_article_by_id,
)
from app.utils.llm_service import build_model_registry, execute_prompt, get_default_model_id

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# PROMPTS
# ----------------------------------------------------------------------

RANKING_PROMPT = """
You are a very experienced cyber threat intelligence analyst specialized in analyzing large amounts of news articles for relevance.
Below is a list of news article headlines. For each headline, consider how relevant it is for cybersecurity and threat intelligence.
News articles have a higher relevance, if there are more news article headlines about the same topic and / or if it describes about active threats or vulnerabilities.
Your task:
1. Identify the 10 most relevant articles from the list (if there are fewer than 10, select them all).
2. Make sure to not list multiple articles about the same topic.
3. Sort them by relevance (most relevant first).
4. Return the result in a JSON array of objects with the following fields:
   - id: the article ID
   - title: the article headline
   - relevance_score: 1 (most relevant) to 10 (least relevant within the top 10)
   - reason: a brief reason for ranking

Only return the JSON, no additional commentary.
List of articles:
<news article headlines>
{articles_list}
</news article headlines>
"""

ANALYSIS_PROMPT = """
You are a very experienced cyber threat intelligence analyst specialized in in creating best in class news article analysis.
Below you will find news article data about a news artcicle.
You will receive the article's title, feed name, and summary text.
Produce a comprehensive analysis in JSON format with the following fields:
{{
  "Risk": "[High / Medium / Low / Informational]",
  "Summary": "[Detailed summary of the article]",
  "Analysis comment": "[Reasoning why the article is relevant]",
  "Action items": ["list of actions"]
  "Source": "Complete url to the article"
}}

The criteria to determine the risk rating are:
<Risk Criteria>
High Risk - Immediate, active threats with high confidence—such as zero-day exploits or unpatched vulnerabilities—that require urgent action to protect critical systems. Severe threats with potential for significant impact where mitigations exist but may be underutilized, necessitating prompt response.
Medium Risk - Emerging vulnerabilities or attack trends that could impact operations under specific conditions, meriting careful monitoring.
Low Risk - Minor issues or outdated threats unlikely to affect core operations, generally limited in scope or impact.
Informational - Background or analytical content that provides context and insights without posing an immediate threat.
</Risk Criteria>

Keep it concise and to the point but not too short. Return only valid JSON.
Article data:
<news article data>
{article_data}
</news article data>
"""

REPORT_MAX_TOKENS = 15000
REPORT_SYSTEM_PROMPT = "You are an experienced cyber threat intelligence analyst."


def _parse_json_response(text: str) -> Any:
    """Parse JSON from LLM response, stripping markdown fences if present"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


async def rank_recent_articles(db: AsyncSession) -> list[dict[str, Any]] | None:
    """Rank recent articles by cybersecurity relevance using an LLM"""
    recent_articles = await get_recent_news_articles(db, time_filter="7d")
    if not recent_articles:
        logger.info("No recent articles found for ranking.")
        return []

    articles_str_list = [f"- (ID: {a.id}) {a.title}" for a in recent_articles]
    if not articles_str_list:
        logger.info("No article titles to process in rank_recent_articles.")
        return []

    articles_list_for_prompt = "\n".join(articles_str_list)

    models = await build_model_registry(db)
    if not models:
        logger.error("No LLM models available for ranking.")
        return []

    model_id = await get_default_model_id(db, "newsfeed_report")

    try:
        user_prompt = RANKING_PROMPT.format(articles_list=articles_list_for_prompt)
        result = await execute_prompt(
            models,
            model_id=model_id,
            system_prompt=REPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=REPORT_MAX_TOKENS,
        )
        ranking_response = _parse_json_response(result)
        return ranking_response[:10]
    except Exception as e:
        logger.exception("Error during LLM call for ranking:")
        return []


async def analyze_article(article_id: int, db: AsyncSession) -> dict[str, Any]:
    """Analyze a single article using an LLM"""
    article = await get_news_article_by_id(db, article_id)
    if not article:
        return {
            "Relevance": "Unknown",
            "Summary": "",
            "full_text": "",
            "Analysis comment": f"Article with ID {article_id} not found.",
            "Action items": []
        }

    article_data = {
        "id": article.id,
        "title": article.title,
        "feedname": article.feedname,
        "summary": article.summary or "",
        "full_text": article.full_text or "",
        "date": str(article.date),
    }

    models = await build_model_registry(db)
    if not models:
        logger.error("No LLM models available for article analysis.")
        return {
            "Relevance": "Unknown",
            "Summary": "",
            "Analysis comment": "No LLM API key configured.",
            "Action items": []
        }

    model_id = await get_default_model_id(db, "newsfeed_report")

    try:
        user_prompt = ANALYSIS_PROMPT.format(article_data=json.dumps(article_data, indent=2))
        result = await execute_prompt(
            models,
            model_id=model_id,
            system_prompt=REPORT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=REPORT_MAX_TOKENS,
        )
        return _parse_json_response(result)
    except Exception as e:
        logger.exception("Error during LLM call for article %s analysis:", article_id)
        return {
            "Relevance": "Unknown",
            "Summary": "",
            "Full Text": "",
            "Analysis comment": f"Exception: {e}",
            "Action items": []
        }


async def analyze_and_rank_top_articles(db: AsyncSession) -> list[dict[str, Any]]:
    """Rank top 10 articles, then analyze each"""
    logger.info("Starting to rank and analyze the top articles.")
    top_articles_ranking = await rank_recent_articles(db)
    if not top_articles_ranking:
        logger.info("No articles returned from rank_recent_articles.")
        return []

    logger.info("Ranked %s articles. Beginning analysis.", len(top_articles_ranking))

    results = []

    for article_info in top_articles_ranking:
        article_id = article_info.get("id")
        if article_id is None:
            logger.warning("Ranked article missing 'id' field; skipping.")
            continue

        analysis = await analyze_article(article_id, db)
        logger.info("Analysis completed for article ID %s.", article_id)

        result_entry = {
            "article_id": article_id,
            "title": article_info.get("title", ""),
            "relevance_score": article_info.get("relevance_score", 99),
            "reason_for_ranking": article_info.get("reason", ""),
            "analysis": analysis
        }
        results.append(result_entry)

    results.sort(key=lambda x: x["relevance_score"])
    logger.info("All articles analyzed. Returning %s results.", len(results))
    return results


async def analyze_top_articles_stream(db: AsyncSession):
    """Async generator for SSE streaming of ranking + analysis"""
    logger.info("Starting SSE stream for top articles ranking + analysis.")
    top_articles_ranking = await rank_recent_articles(db)

    if not top_articles_ranking:
        yield json.dumps({
            "type": "ranking",
            "articles": [],
            "info": "No ranked articles found."
        })
        yield json.dumps({
            "type": "complete",
            "message": "All analysis done"
        })
        return

    yield json.dumps({
        "type": "ranking",
        "articles": top_articles_ranking
    })

    for article_info in top_articles_ranking:
        article_id = article_info.get("id")
        if article_id is None:
            logger.warning("Skipping article in SSE stream: missing ID.")
            continue

        analysis = await analyze_article(article_id, db)
        result_entry = {
            "article_id": article_id,
            "title": article_info.get("title", ""),
            "relevance_score": article_info.get("relevance_score", 99),
            "reason_for_ranking": article_info.get("reason", ""),
            "analysis": analysis
        }

        yield json.dumps({
            "type": "analysis",
            "article_result": result_entry
        })

    yield json.dumps({
        "type": "complete",
        "message": "All analysis done"
    })
