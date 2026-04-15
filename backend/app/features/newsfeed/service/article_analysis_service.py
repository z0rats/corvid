import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.crud.news_articles_crud import get_news_article_by_id, update_news_article
from app.features.newsfeed.models.newsfeed_models import NewsArticle
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


async def analyze_article_with_llm(
    db: AsyncSession,
    article_id: int,
    model_id: str,
    temperature: float,
    max_tokens: int,
    use_cti_settings: bool,
    force: bool,
) -> dict:
    """Orchestrate LLM-based analysis of a news article"""
    logger.info(
        "Starting analysis for article ID: %d with model %s, force=%s, use_cti_settings=%s",
        article_id, model_id, force, use_cti_settings,
    )

    news_article_record = await get_news_article_by_id(db=db, article_id=article_id)
    if not news_article_record:
        raise ValueError(f"Article with ID {article_id} not found")

    if news_article_record.analysis_result and not force:
        try:
            return {
                "message": "Analysis already completed",
                "analysis_result": json.loads(news_article_record.analysis_result),
            }
        except json.JSONDecodeError:
            logger.warning("Could not parse stored analysis result as JSON, forcing reanalysis")

    cti_settings = await _load_cti_settings(db) if use_cti_settings else None
    cti_profile_text = build_cti_profile_text(cti_settings)

    newsfeed_item = extract_article_content(news_article_record)
    system_prompt, user_prompt = build_analysis_prompts(newsfeed_item, cti_profile_text)

    models = await build_model_registry(db)
    analysis_text = await execute_prompt(
        models,
        model_id=model_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    analysis_json = _parse_llm_json_response(analysis_text)
    formatted_result = _build_formatted_result(analysis_json)

    await update_news_article(db=db, article_id=article_id, analysis_result=json.dumps(formatted_result))

    response = {"message": "Analysis completed", "analysis_result": formatted_result}
    if use_cti_settings and cti_settings:
        response["cti_settings_used"] = True

    return response
