import logging
import mimetypes

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.llm_service import (
    build_model_registry,
    execute_structured_prompt,
    get_default_model_id,
)

from ..schemas.image_schemas import (
    ImageGeolocationAIResult,
    ImageGeolocationResponse,
    TextSignal,
)
from .geo_clues_service import format_reference, reference_countries
from .text_signals_service import compute_text_signals

logger = logging.getLogger(__name__)

MODULE_KEY = "image_geolocation"

SYSTEM_PROMPT = (
    "You are a GeoINT (geolocation intelligence) analyst. Given a single photo, identify visual "
    "clues that hint at where it was taken - road markings and signage, license plates, driving "
    "side, architecture style, vegetation and climate, terrain, language on signs, utility poles "
    "and power infrastructure, and similar details. Rank your best-guess locations by confidence "
    "(a country or region, not a precise address unless something in the photo makes it "
    "unambiguous), and always explain which observed clues support each candidate. Never present "
    "a guess as certain fact - state this is a hypothesis based on visual cues only, and note "
    "when the photo lacks enough distinguishing detail to narrow things down."
)

USER_PROMPT = (
    "Analyze this photo for geolocation clues. List the specific visual details you observed "
    "and what each one suggests, then give your ranked location candidates with your reasoning "
    "for each. Also transcribe every legible piece of text in the photo (signs, shop names, "
    "license plates, phone numbers, web addresses, prices) into visible_text, one line each, "
    "exactly as written in its original script and never translated; leave it empty if there "
    "is none."
)

REFINE_SYSTEM_PROMPT = (
    SYSTEM_PROMPT + " You are now cross-checking a first-pass analysis. Compare the photo against "
    "the reference facts for each country listed: confirm a candidate only when the photo shows a "
    "matching tell (plate format, road paint, script, signs), lower or drop it when the photo "
    "contradicts the reference, and add a country from the list if the evidence now favours it. "
    "The reference is general knowledge about typical conventions, not proof - old and new "
    "styles coexist - so never cite a tell the photo does not actually show."
)

REFINE_USER_PROMPT = (
    "First-pass analysis (JSON):\n{first_pass}\n\n"
    "Hints computed from the transcribed text:\n{signals}\n\n"
    "Reference facts per country:\n{reference}\n\n"
    "Re-examine the photo and return the revised ranked candidates and clues. Keep visible_text "
    "as in the first pass."
)

DEFAULT_MEDIA_TYPE = "image/jpeg"


def _guess_media_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type if mime_type and mime_type.startswith("image/") else DEFAULT_MEDIA_TYPE


async def analyze_image_location(
    filename: str,
    image_data: bytes,
    db: AsyncSession,
    model_id: str | None = None,
) -> ImageGeolocationResponse:
    """Generate an AI location hypothesis for a photo, with supporting reasoning."""
    if not model_id:
        model_id = await get_default_model_id(db, MODULE_KEY)

    logger.info(
        "Starting AI geolocation analysis of '%s' (%d bytes) with model %s",
        filename,
        len(image_data),
        model_id,
    )

    models = await build_model_registry(db)
    media_type = _guess_media_type(filename)

    result = await execute_structured_prompt(
        models,
        model_id=model_id,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        output_type=ImageGeolocationAIResult,
        image_data=image_data,
        image_media_type=media_type,
    )
    text_signals = compute_text_signals(result.visible_text)
    countries = reference_countries(result.candidates, text_signals)
    if countries:
        refined = await _cross_check(
            models, model_id, result, text_signals, countries, image_data, media_type
        )
        if refined is not None:
            result = refined.model_copy(update={"visible_text": result.visible_text})
        else:
            countries = []

    return ImageGeolocationResponse(
        **result.model_dump(),
        text_signals=text_signals,
        reference_countries=countries,
        model_used=model_id,
    )


async def _cross_check(
    models: dict,
    model_id: str,
    first_pass: ImageGeolocationAIResult,
    text_signals: list[TextSignal],
    countries: list[str],
    image_data: bytes,
    media_type: str,
) -> ImageGeolocationAIResult | None:
    """Second pass against per-country reference clues; None keeps the first-pass result."""
    signals = [
        f"{s.kind} {s.matched}: {', '.join([*s.countries, *s.languages]) or 'n/a'}"
        for s in text_signals
    ]
    try:
        return await execute_structured_prompt(
            models,
            model_id=model_id,
            system_prompt=REFINE_SYSTEM_PROMPT,
            user_prompt=REFINE_USER_PROMPT.format(
                first_pass=first_pass.model_dump_json(exclude={"visible_text"}),
                signals="\n".join(signals) or "none",
                reference=format_reference(countries),
            ),
            output_type=ImageGeolocationAIResult,
            image_data=image_data,
            image_media_type=media_type,
        )
    except ValueError:
        logger.warning(
            "Geolocation cross-check failed, keeping the first-pass result", exc_info=True
        )
        return None
