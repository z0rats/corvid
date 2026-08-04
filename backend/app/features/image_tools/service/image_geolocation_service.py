import logging
import mimetypes

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.llm_service import build_model_registry, execute_structured_prompt, get_default_model_id
from ..schemas.image_schemas import ImageGeolocationAIResult, ImageGeolocationResponse

logger = logging.getLogger(__name__)

MODULE_KEY = "image_geolocation"

SYSTEM_PROMPT = (
    "You are a GeoINT (geolocation intelligence) analyst. Given a single photo, identify visual "
    "clues that hint at where it was taken - road markings and signage, license plates, driving "
    "side, architecture style, vegetation and climate, terrain, language on signs, utility poles "
    "and power infrastructure, and similar details. Rank your best-guess locations by confidence "
    "(a country or region, not a precise address unless something in the photo makes it unambiguous), "
    "and always explain which observed clues support each candidate. Never present a guess as "
    "certain fact - state this is a hypothesis based on visual cues only, and note when the photo "
    "lacks enough distinguishing detail to narrow things down."
)

USER_PROMPT = (
    "Analyze this photo for geolocation clues. List the specific visual details you observed and "
    "what each one suggests, then give your ranked location candidates with your reasoning for each."
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

    logger.info("Starting AI geolocation analysis of '%s' (%d bytes) with model %s", filename, len(image_data), model_id)

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
    return ImageGeolocationResponse(**result.model_dump(), model_used=model_id)
