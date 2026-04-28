"""MITRE ATT&CK enrichment service for news articles"""

import logging

from app.features.newsfeed.schemas.newsfeed_schemas import ThreatIntelEnrichment
from app.utils.llm_service import execute_structured_prompt

logger = logging.getLogger(__name__)

MITRE_ENRICHMENT_SYSTEM_PROMPT = """
You are an expert MITRE ATT&CK analyst. Your task is to extract structured threat intelligence
from cybersecurity news articles and map findings to the MITRE ATT&CK framework.

Rules:
- Only extract threat actors, TTPs, and software that are explicitly mentioned or strongly implied by the article content.
- Do NOT speculate or hallucinate MITRE IDs. Only include IDs you are confident are correct.
- Set has_mitre_data to false when the article has no meaningful ATT&CK relevance (e.g. general security news, policy articles, product announcements without technical detail).
- Use the correct MITRE ATT&CK URL format: https://attack.mitre.org/techniques/TXXXX/ for techniques, https://attack.mitre.org/groups/GXXXX/ for groups, https://attack.mitre.org/software/SXXXX/ for software.
- For sub-techniques, use the format: https://attack.mitre.org/techniques/TXXXX/XXX/
- Be precise with kill chain phases: reconnaissance, weaponization, delivery, exploitation, installation, command-and-control, actions-on-objectives.
- Focus on actionable detection opportunities that security teams can implement.
""".strip()


def build_mitre_enrichment_prompt(newsfeed_item: dict, cti_profile_text: str) -> str:
    """Build the user prompt for MITRE ATT&CK enrichment"""
    return f"""Analyze the following cybersecurity news article and extract MITRE ATT&CK mappings.

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

Extract all applicable MITRE ATT&CK threat intelligence from this article. If the article does not describe specific threats, attack techniques, or threat actors, set has_mitre_data to false and leave all lists empty."""


async def enrich_article_with_mitre(
    models: dict,
    model_id: str,
    newsfeed_item: dict,
    cti_profile_text: str,
    temperature: float,
    max_tokens: int,
) -> ThreatIntelEnrichment:
    """Extract MITRE ATT&CK enrichment from a news article using structured LLM output"""
    user_prompt = build_mitre_enrichment_prompt(newsfeed_item, cti_profile_text)

    return await execute_structured_prompt(
        models,
        model_id=model_id,
        system_prompt=MITRE_ENRICHMENT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_type=ThreatIntelEnrichment,
        temperature=temperature,
        max_tokens=max_tokens,
    )
