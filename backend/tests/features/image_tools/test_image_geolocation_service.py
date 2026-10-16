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

        self.calls = []
        self.second_pass_error = None

        async def fake_execute_structured_prompt(models, **kwargs):
            self.captured_kwargs = kwargs
            self.calls.append(kwargs)
            if len(self.calls) == 2 and self.second_pass_error:
                raise self.second_pass_error
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
                visible_text=["Београд", "+381 11 123 4567"],
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

    def test_computes_text_signals_from_the_transcription(self):
        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg",
                image_data=b"fake-bytes",
                db=None,
            )
        )

        assert result.visible_text == ["Београд", "+381 11 123 4567"]
        by_kind = {signal.kind: signal for signal in result.text_signals}
        assert "RS" in by_kind["script"].countries
        assert by_kind["phone"].countries == ["RS"]

    def test_cross_checks_against_reference_clues_of_candidate_countries(self):
        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg", image_data=b"fake-bytes", db=None
            )
        )

        assert len(self.calls) == 2
        second = self.calls[1]
        assert second["image_data"] == b"fake-bytes"
        assert "Serbia (RS)" in second["user_prompt"]
        assert "Cyrillic" in second["user_prompt"]
        assert "visible_text" not in second["user_prompt"].split("Hints computed")[0]
        assert result.reference_countries == ["RS"]

    def test_keeps_first_pass_transcription_even_if_second_pass_drops_it(self, monkeypatch):
        outputs = [
            ImageGeolocationAIResult(
                candidates=[GeoCandidate(location="Serbia", confidence=0.5, reasoning="r")],
                clues=[],
                visible_text=["Београд"],
            ),
            ImageGeolocationAIResult(
                candidates=[GeoCandidate(location="Serbia", confidence=0.8, reasoning="r2")],
                clues=[],
                visible_text=[],
            ),
        ]

        async def sequenced(models, **kwargs):
            return outputs.pop(0)

        monkeypatch.setattr(image_geolocation_service, "execute_structured_prompt", sequenced)

        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg", image_data=b"x", db=None
            )
        )

        assert result.candidates[0].confidence == 0.8
        assert result.visible_text == ["Београд"]

    def test_second_pass_failure_falls_back_to_first_pass(self):
        self.second_pass_error = ValueError("model rejected the prompt")

        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg", image_data=b"fake-bytes", db=None
            )
        )

        assert len(self.calls) == 2
        assert result.candidates[0].location == "Serbia"
        assert result.reference_countries == []

    def test_skips_cross_check_when_no_country_is_recognised(self, monkeypatch):
        calls = []

        async def vague(models, **kwargs):
            calls.append(kwargs)
            return ImageGeolocationAIResult(
                candidates=[
                    GeoCandidate(location="Somewhere in Europe", confidence=0.2, reasoning="r")
                ],
                clues=[],
            )

        monkeypatch.setattr(image_geolocation_service, "execute_structured_prompt", vague)

        result = _run(
            image_geolocation_service.analyze_image_location(
                filename="street.jpg", image_data=b"x", db=None
            )
        )

        assert len(calls) == 1
        assert result.reference_countries == []
