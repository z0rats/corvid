import asyncio

import pytest

from app.features.image_tools.schemas.image_schemas import (
    GeoCandidate,
    GeoClue,
    ImageGeolocationAIResult,
)
from app.features.image_tools.service import image_geolocation_service


def _run(coro):
    return asyncio.run(coro)


class TestGuessMediaType:
    def test_recognizes_jpeg(self):
        assert image_geolocation_service._guess_media_type("photo.jpg") == "image/jpeg"

    def test_recognizes_png(self):
        assert image_geolocation_service._guess_media_type("photo.png") == "image/png"

    def test_falls_back_to_default_for_unknown_extension(self):
        assert image_geolocation_service._guess_media_type("photo.xyz") == "image/jpeg"


class TestAnalyzeImageLocation:
    @pytest.fixture(autouse=True)
    def stub_llm_dependencies(self, monkeypatch):
        self.captured_kwargs = {}

        async def fake_get_default_model_id(db, module_key):
            assert module_key == "image_geolocation"
            return "claude-sonnet-4-6"

        async def fake_build_model_registry(db):
            return {"claude-sonnet-4-6": object(), "gpt-4o": object()}

        async def fake_execute_structured_prompt(models, **kwargs):
            self.captured_kwargs = kwargs
            return ImageGeolocationAIResult(
                candidates=[
                    GeoCandidate(
                        location="Serbia", confidence=0.6, reasoning="road markings + signage"
                    )
                ],
                clues=[
                    GeoClue(
                        category="signage_language",
                        observation="Cyrillic text",
                        supports="Serbia/Balkans",
                    )
                ],
                caveats="Hypothesis only, not confirmed.",
            )

        monkeypatch.setattr(
            image_geolocation_service, "get_default_model_id", fake_get_default_model_id
        )
        monkeypatch.setattr(
            image_geolocation_service, "build_model_registry", fake_build_model_registry
        )
        monkeypatch.setattr(
            image_geolocation_service, "execute_structured_prompt", fake_execute_structured_prompt
        )

    def test_fills_in_model_used_from_resolved_default(self):
        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg",
                image_data=b"fake-bytes",
                db=None,
            )
        )

        assert result.model_used == "claude-sonnet-4-6"
        assert result.candidates[0].location == "Serbia"
        assert result.clues[0].category == "signage_language"
        assert result.caveats == "Hypothesis only, not confirmed."

    def test_passes_image_bytes_and_guessed_media_type_through(self):
        _run(
            image_geolocation_service.analyze_image_location(
                filename="street.png",
                image_data=b"fake-bytes",
                db=None,
            )
        )

        assert self.captured_kwargs["image_data"] == b"fake-bytes"
        assert self.captured_kwargs["image_media_type"] == "image/png"

    def test_respects_explicit_model_id_without_resolving_default(self, monkeypatch):
        async def fail_if_called(db, module_key):
            raise AssertionError("should not resolve a default model when one is explicitly given")

        monkeypatch.setattr(image_geolocation_service, "get_default_model_id", fail_if_called)

        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg",
                image_data=b"fake-bytes",
                db=None,
                model_id="gpt-4o",
            )
        )

        assert result.model_used == "gpt-4o"
