import asyncio
import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.news_articles_crud import get_news_article_by_id, update_news_article
from app.features.newsfeed.models.newsfeed_models import NewsArticle
from app.features.newsfeed.service.mitre_enrichment_service import enrich_article_with_mitre
from app.core.settings.cti_profile.crud.cti_profile_crud import get_cti_settings
from app.utils.llm_service import build_model_registry, execute_prompt

logger = logging.getLogger(__name__)

DEFAULT_CTI_PROFILE = (
    "Default CTI Profile: General cybersecurity monitoring with focus on "
    "critical vulnerabilities, active threats, and major security incidents."
)

SYSTEM_PROMPT = """
You are an expert cybersecurity analyst specializing in threat intelligence, vulnerability analysis, and security operations.
Your task is to analyze cybersecurity news articles and determine their relevance and implications.
Provide clear, concise, and actionable insights that security teams can use to improve their security posture.
"""

RELEVANCE_INDICATORS = {
    "None": "\U0001f7e2",
    "Low": "\U0001f7e1",
    "Medium": "\U0001f7e0",
    "High": "\U0001f534",
}


def format_analysis_to_markdown(analysis_json: dict) -> str:
    """Convert structured analysis JSON into readable markdown"""
    lines = []

    relevance = analysis_json.get("relevance", "Unknown")
    indicator = RELEVANCE_INDICATORS.get(relevance, "\u26aa")
    lines.append(f"**Relevance:** {indicator} {relevance}")
    lines.append("")

    for field, label in [("reason", "Reason"), ("summary", "Summary")]:
        if field in analysis_json:
            lines.append(f"**{label}:**")
            lines.append(f"{analysis_json[field]}")
            lines.append("")

    for field, label in [
        ("key_points", "Key Points"),
        ("action_items", "Action Items"),
        ("affected_systems", "Affected Systems"),
    ]:
        if field in analysis_json and analysis_json[field]:
            lines.append(f"**{label}:**")
            for item in analysis_json[field]:
                lines.append(f"- {item}")
            lines.append("")

    return "\n".join(lines).rstrip("\n")


def _dict_to_markdown_lines(data: dict, level: int = 0) -> list[str]:
    """Convert a CTI profile settings dict into indented markdown.

    Handles feature-toggle dicts with 'enabled'/'details' keys and skips disabled entries.
    """
    lines = []
    indent = "  " * level

    for key, value in data.items():
        if isinstance(value, dict) and value.get("enabled") is False:
            continue
        if isinstance(value, bool) and not value:
            continue

        heading = f"## {key.title()}" if level == 0 else f"{indent}- **{key.title()}**:"

        if isinstance(value, dict):
            if value.get("enabled") and "details" in value:
                lines.append(f"{heading} {value['details']}")
            else:
                filtered = {k: v for k, v in value.items() if k != "enabled"}
                if filtered:
                    lines.append(heading)
                    lines.extend(_dict_to_markdown_lines(filtered, level + 1))
        elif isinstance(value, list):
            lines.append(heading)
            for item in value:
                if isinstance(item, dict):
                    lines.extend(_dict_to_markdown_lines(item, level + 1))
                else:
                    lines.append(f"{indent}  - {item}")
        elif isinstance(value, bool):
            lines.append(heading.rstrip(":"))
        else:
            lines.append(f"{heading} {value}")

    return lines


def build_cti_profile_text(cti_settings) -> str:
    """Build markdown CTI profile text from settings database record"""
    if not cti_settings or not cti_settings.settings_data:
        return DEFAULT_CTI_PROFILE

    try:
        settings_dict = json.loads(cti_settings.settings_data)
    except json.JSONDecodeError:
        logger.warning("Failed to parse CTI settings JSON, using default profile")
        return DEFAULT_CTI_PROFILE

    try:
        markdown_lines = _dict_to_markdown_lines(settings_dict)
    except Exception as e:
        logger.error("Error converting CTI settings to markdown: %s", str(e))
        return DEFAULT_CTI_PROFILE

    if not markdown_lines:
        return DEFAULT_CTI_PROFILE

    markdown_lines.insert(0, "# CTI Profile")
    markdown_lines.append("")
    profile_text = "\n".join(markdown_lines)
    logger.debug("Generated CTI profile markdown:\n%s", profile_text)
    return profile_text


def build_analysis_prompts(newsfeed_item: dict, cti_profile_text: str) -> tuple[str, str]:
    """Build the system and user prompts for article analysis"""
    user_prompt = f"""
You are an AI assistant that analyzes a news article based on a user's Cyber Threat Intelligence (CTI) profile. Below you will find the CTI profile, the news article and instructions for your analysis.

<CTI Profile>
{cti_profile_text}
</CTI Profile>

<News Article>
Title: {newsfeed_item['title']}
Source: {newsfeed_item['source']}
Date: {newsfeed_item['date']}

Content:
{newsfeed_item['content']}
</News Article>

<Instructions>
Check if the news article is relevant based on the CTI profile above.
Analyze and categorize the relevance of this article.
Provide your response as valid JSON with the following structure:
</Instructions>

{{"relevance": "None | Low | Medium | High",
"reason": "Detailed explanation of why this article is relevant or not relevant to the CTI profile",
"summary": "Concise summary of the article (2-3 sentences)",
"key_points": ["Key point 1", "Key point 2", "Key point 3"],
"action_items": ["Possible action 1", "Possible action 2"],
"affected_systems": ["System type 1", "System type 2"]}}

Provide only the JSON response without any additional text, markdown formatting, or explanations.
"""
    return SYSTEM_PROMPT, user_prompt


def extract_article_content(news_article_record: NewsArticle) -> dict:
    """Extract title, source, date, and content from a news article record"""
    content = news_article_record.full_text or news_article_record.summary
    if not content:
        raise ValueError("Article has no content")

    return {
        "title": news_article_record.title or "No title available",
        "source": news_article_record.feedname or "Unknown source",
        "date": news_article_record.date or "Unknown date",
        "content": content,
    }


def _parse_llm_json_response(analysis_text: str) -> dict:
    """Parse JSON from LLM response, with fallback regex extraction"""
    try:
        return json.loads(analysis_text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse response as JSON directly, attempting to extract JSON")

    json_match = re.search(r"(\{.*\})", analysis_text, re.DOTALL)
    if not json_match:
        raise ValueError("Could not extract valid JSON from the model response")

    try:
        return json.loads(json_match.group(1))
    except json.JSONDecodeError:
        logger.error("Extracted text is not valid JSON")
        raise ValueError("Could not extract valid JSON from the model response")


def _build_formatted_result(analysis_json: dict) -> dict:
    """Build the formatted result dict with markdown and raw JSON"""
    return {
        "markdown": format_analysis_to_markdown(analysis_json),
        "raw": analysis_json,
    }


async def _load_cti_settings(db: AsyncSession):
    """Load CTI settings from database with error handling"""
    try:
        cti_settings = await get_cti_settings(db=db)
        if not cti_settings or not cti_settings.settings_data:
            logger.warning("CTI settings not found or empty. Using default analysis.")
            return None
        return cti_settings
    except Exception as e:
        logger.error("Error retrieving CTI settings: %s", str(e))
        logger.warning("Continuing with default analysis without CTI settings")
        return None


def _parse_stored_mitre_data(mitre_attack_str: str | None) -> dict | None:
    """Parse stored mitre_attack JSON string, returning None if empty or invalid"""
    if not mitre_attack_str:
        return None
    try:
        return json.loads(mitre_attack_str)
    except json.JSONDecodeError:
        logger.warning("Could not parse stored mitre_attack data as JSON")
        return None


async def _run_concurrent_analysis(
    models: dict,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    newsfeed_item: dict,
    cti_profile_text: str,
    temperature: float,
    max_tokens: int,
) -> tuple:
    """Run general analysis and MITRE enrichment concurrently"""
    analysis_task = execute_prompt(
        models, model_id=model_id,
        system_prompt=system_prompt, user_prompt=user_prompt,
        temperature=temperature, max_tokens=max_tokens,
    )
    mitre_task = enrich_article_with_mitre(
        models, model_id=model_id,
        newsfeed_item=newsfeed_item, cti_profile_text=cti_profile_text,
        temperature=temperature, max_tokens=max(max_tokens, 3000),
    )
    return await asyncio.gather(analysis_task, mitre_task, return_exceptions=True)


async def _run_mitre_only(
    models: dict,
    model_id: str,
    newsfeed_item: dict,
    cti_profile_text: str,
    temperature: float,
    max_tokens: int,
) -> dict | None:
    """Run only the MITRE enrichment when general analysis is already cached"""
    try:
        result = await enrich_article_with_mitre(
            models, model_id=model_id,
            newsfeed_item=newsfeed_item, cti_profile_text=cti_profile_text,
            temperature=temperature, max_tokens=max(max_tokens, 3000),
        )
        return result.model_dump() if result.has_mitre_data else None
    except Exception as e:
        logger.error("MITRE enrichment failed: %s", e)
        return None


def _resolve_mitre_result(mitre_result) -> dict | None:
    """Extract MITRE enrichment dict from the gather result, handling errors"""
    if isinstance(mitre_result, Exception):
        logger.error("MITRE enrichment failed: %s", mitre_result)
        return None
    if not mitre_result.has_mitre_data:
        return None
    return mitre_result.model_dump()


async def analyze_article_with_llm(
    db: AsyncSession,
    article_id: int,
    model_id: str,
    temperature: float,
    max_tokens: int,
    use_cti_settings: bool,
    force: bool,
    mode: str = "all",
) -> dict:
    """Orchestrate LLM-based analysis of a news article"""
    logger.info(
        "Starting analysis for article ID: %d with model %s, force=%s, mode=%s",
        article_id, model_id, force, mode,
    )

    news_article_record = await get_news_article_by_id(db=db, article_id=article_id)
    if not news_article_record:
        raise ValueError(f"Article with ID {article_id} not found")

    run_analysis = mode in ("all", "analysis")
    run_mitre = mode in ("all", "mitre")

    has_cached_analysis = bool(news_article_record.analysis_result)
    has_cached_mitre = bool(news_article_record.mitre_attack)

    if not force:
        analysis_cached = has_cached_analysis or not run_analysis
        mitre_cached = has_cached_mitre or not run_mitre
        if analysis_cached and mitre_cached:
            try:
                return {
                    "message": "Analysis already completed",
                    "analysis_result": json.loads(news_article_record.analysis_result) if has_cached_analysis else None,
                    "mitre_attack": _parse_stored_mitre_data(news_article_record.mitre_attack),
                }
            except json.JSONDecodeError:
                logger.warning("Could not parse stored results as JSON, forcing reanalysis")

    cti_settings = await _load_cti_settings(db) if use_cti_settings else None
    cti_profile_text = build_cti_profile_text(cti_settings)
    newsfeed_item = extract_article_content(news_article_record)
    models = await build_model_registry(db)

    formatted_result = None
    mitre_data = None

    if run_analysis and run_mitre:
        system_prompt, user_prompt = build_analysis_prompts(newsfeed_item, cti_profile_text)
        analysis_result, mitre_result = await _run_concurrent_analysis(
            models, model_id, system_prompt, user_prompt,
            newsfeed_item, cti_profile_text, temperature, max_tokens,
        )
        if isinstance(analysis_result, Exception):
            raise analysis_result
        analysis_json = _parse_llm_json_response(analysis_result)
        formatted_result = _build_formatted_result(analysis_json)
        mitre_data = _resolve_mitre_result(mitre_result)
    elif run_analysis:
        system_prompt, user_prompt = build_analysis_prompts(newsfeed_item, cti_profile_text)
        analysis_text = await execute_prompt(
            models, model_id=model_id,
            system_prompt=system_prompt, user_prompt=user_prompt,
            temperature=temperature, max_tokens=max_tokens,
        )
        analysis_json = _parse_llm_json_response(analysis_text)
        formatted_result = _build_formatted_result(analysis_json)
    elif run_mitre:
        mitre_data = await _run_mitre_only(
            models, model_id, newsfeed_item, cti_profile_text, temperature, max_tokens,
        )

    update_kwargs = {}
    if formatted_result is not None:
        update_kwargs["analysis_result"] = json.dumps(formatted_result)
    if run_mitre:
        update_kwargs["mitre_attack"] = json.dumps(mitre_data) if mitre_data else None

    if update_kwargs:
        await update_news_article(db=db, article_id=article_id, **update_kwargs)

    response = {
        "message": "Analysis completed",
        "analysis_result": formatted_result or (json.loads(news_article_record.analysis_result) if has_cached_analysis else None),
        "mitre_attack": mitre_data or _parse_stored_mitre_data(news_article_record.mitre_attack),
    }
    if use_cti_settings and cti_settings:
        response["cti_settings_used"] = True

    return response
