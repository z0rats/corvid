import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.llm_service import build_model_registry, execute_prompt, get_default_model_id

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert cybersecurity analyst specializing in email security, phishing detection, "
    "and social engineering analysis. Analyze the provided email message body and identify potential "
    "security threats, suspicious patterns, and indicators of compromise. "
    "Provide clear, actionable insights."
)

USER_PROMPT_TEMPLATE = """Analyze the following email message body for security concerns:

<Email Body>
{email_body}
</Email Body>

Provide your analysis covering:
1. **Overall Assessment** - Is this email likely legitimate, suspicious, or malicious?
2. **Threat Indicators** - Any phishing attempts, social engineering tactics, or suspicious elements
3. **Suspicious Links/References** - Any suspicious URLs, domains, or references found in the text
4. **Language Analysis** - Urgency tactics, impersonation attempts, or manipulation techniques
5. **Recommendations** - What actions should the recipient take?

Format your response in clear markdown."""


async def analyze_email_body(
    email_body: str,
    db: AsyncSession,
    model_id: str | None = None,
    temperature: float = 1.0,
) -> str:
    """Analyze an email message body using an LLM for security threats"""
    if not model_id:
        model_id = await get_default_model_id(db, "email_analyzer")

    logger.info("Starting AI analysis of email body (%d chars) with model %s", len(email_body), model_id)

    models = await build_model_registry(db)
    user_prompt = USER_PROMPT_TEMPLATE.format(email_body=email_body)

    return await execute_prompt(
        models,
        model_id=model_id,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=temperature,
    )
