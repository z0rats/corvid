import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.features.image_tools.routers import image_routes
from app.features.image_tools.schemas.image_schemas import (
    GeoCandidate,
    GeoClue,
    ImageGeolocationResponse,
)


@pytest.fixture
def client():
    """A minimal FastAPI app exposing only the image_tools router.

    Avoids spinning up the full application (database, scheduler, other
    feature routers) so this test only exercises the image_tools API contract.
    get_read_db is overridden with a no-op since none of these tests hit a real
    database - /geolocate's service call is monkeypatched per-test instead.
    """
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(image_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check_reports_supported_formats(self, client):
        response = client.get("/api/image/health")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "image_tools"
        assert body["status"] == "healthy"
        assert ".jpg" in body["supported_formats"]


class TestAnalyzeEndpoint:
    def test_analyzes_valid_image(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/analyze",
            files={"file": ("photo.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["file_info"]["filename"] == "photo.jpg"
        assert body["file_info"]["format"] == "JPEG"
        assert "md5" in body["hashes"]

    def test_extracts_gps_from_uploaded_image(self, client, jpeg_with_gps, monkeypatch):
        async def fake_reverse_geocode(latitude, longitude):
            return None

        monkeypatch.setattr(image_routes, "reverse_geocode", fake_reverse_geocode)

        response = client.post(
            "/api/image/analyze",
            files={"file": ("gps.jpg", jpeg_with_gps, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["gps"] is not None
        assert body["gps"]["latitude"] == pytest.approx(40.446194, abs=1e-5)

    def test_populates_gps_address_from_reverse_geocoding(self, client, jpeg_with_gps, monkeypatch):
        async def fake_reverse_geocode(latitude, longitude):
            return "123 Fake Street, Pittsburgh, PA"

        monkeypatch.setattr(image_routes, "reverse_geocode", fake_reverse_geocode)

        response = client.post(
            "/api/image/analyze",
            files={"file": ("gps.jpg", jpeg_with_gps, "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.json()["gps"]["address"] == "123 Fake Street, Pittsburgh, PA"

    def test_does_not_geocode_when_no_gps_present(self, client, plain_jpeg_bytes, monkeypatch):
        calls = []

        async def fake_reverse_geocode(latitude, longitude):
            calls.append((latitude, longitude))
            return "should not be called"

        monkeypatch.setattr(image_routes, "reverse_geocode", fake_reverse_geocode)

        response = client.post(
            "/api/image/analyze",
            files={"file": ("photo.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.json().get("gps") is None
        assert calls == []

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            "/api/image/analyze",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_rejects_empty_file(self, client):
        response = client.post(
            "/api/image/analyze",
            files={"file": ("photo.jpg", b"", "image/jpeg")},
        )

        assert response.status_code == 400

    def test_rejects_corrupt_image_with_valid_extension(self, client):
        response = client.post(
            "/api/image/analyze",
            files={"file": ("photo.jpg", b"not actually a jpeg", "image/jpeg")},
        )

        assert response.status_code == 422

    def test_missing_file_is_rejected(self, client):
        response = client.post("/api/image/analyze")

        assert response.status_code == 422


class TestGeolocateEndpoint:
    @pytest.fixture
    def stub_analysis(self, monkeypatch):
        """Stubs the geolocation service so these tests exercise the HTTP contract only."""

        async def fake_analyze_image_location(filename, image_data, db, model_id=None):
            return ImageGeolocationResponse(
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
                model_used="claude-sonnet-4-6",
            )

        monkeypatch.setattr(image_routes, "analyze_image_location", fake_analyze_image_location)

    def test_geolocates_valid_image(self, client, plain_jpeg_bytes, stub_analysis):
        response = client.post(
            "/api/image/geolocate",
            files={"file": ("street.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["model_used"] == "claude-sonnet-4-6"
        assert body["candidates"][0]["location"] == "Serbia"
        assert body["clues"][0]["category"] == "signage_language"

    def test_rejects_disallowed_extension(self, client, stub_analysis):
        response = client.post(
            "/api/image/geolocate",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400

    def test_missing_file_is_rejected(self, client, stub_analysis):
        response = client.post("/api/image/geolocate")

        assert response.status_code == 422

    def test_maps_value_error_from_service_to_422(self, client, plain_jpeg_bytes, monkeypatch):
        async def fake_analyze_image_location(filename, image_data, db, model_id=None):
            raise ValueError("No LLM models available (no API keys configured)")

        monkeypatch.setattr(image_routes, "analyze_image_location", fake_analyze_image_location)

        response = client.post(
            "/api/image/geolocate",
            files={"file": ("street.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "No LLM models available (no API keys configured)"


class TestStructureEndpoint:
    def test_analyzes_valid_jpeg(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/structure",
            files={"file": ("photo.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["markers"][0]["marker_type"] == "SOI"
        assert body["frame"]["width"] == 100
        assert len(body["quantization_tables"]) >= 1

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            "/api/image/structure",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400

    def test_rejects_non_jpeg_image(self, client, png_bytes):
        response = client.post(
            "/api/image/structure",
            files={"file": ("photo.png", png_bytes, "image/png")},
        )

        assert response.status_code == 422
        assert "JPEG" in response.json()["detail"]

    def test_missing_file_is_rejected(self, client):
        response = client.post("/api/image/structure")

        assert response.status_code == 422


class TestVisualAnalysisEndpoint:
    def test_analyzes_valid_image(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/visual-analysis",
            files={"file": ("photo.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert len(body["histograms"]["red"]) == 256
        assert body["vectorscope"]["bin_count"] == 64

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            "/api/image/visual-analysis",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400

    def test_rejects_corrupt_image(self, client):
        response = client.post(
            "/api/image/visual-analysis",
            files={"file": ("photo.jpg", b"not actually a jpeg", "image/jpeg")},
        )

        assert response.status_code == 422

    def test_missing_file_is_rejected(self, client):
        response = client.post("/api/image/visual-analysis")

        assert response.status_code == 422


class TestAnomaliesEndpoint:
    def test_reports_no_findings_for_a_clean_image(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/anomalies",
            files={"file": ("photo.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["findings"] == []
        assert body["checks_run"] > 0

    def test_flags_trailing_data(self, client, plain_jpeg_bytes):
        tampered = plain_jpeg_bytes + b"appended data"

        response = client.post(
            "/api/image/anomalies",
            files={"file": ("photo.jpg", tampered, "image/jpeg")},
        )

        assert response.status_code == 200
        checks = {f["check"] for f in response.json()["findings"]}
        assert "trailing_data" in checks

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            "/api/image/anomalies",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400

    def test_rejects_corrupt_image(self, client):
        response = client.post(
            "/api/image/anomalies",
            files={"file": ("photo.jpg", b"not actually a jpeg", "image/jpeg")},
        )

        assert response.status_code == 422

    def test_missing_file_is_rejected(self, client):
        response = client.post("/api/image/anomalies")

        assert response.status_code == 422


class TestCompareEndpoint:
    def test_compares_two_valid_images(self, client, plain_jpeg_bytes, jpeg_with_software_tag):
        response = client.post(
            "/api/image/compare",
            files={
                "file_left": ("a.jpg", plain_jpeg_bytes, "image/jpeg"),
                "file_right": ("b.jpg", jpeg_with_software_tag, "image/jpeg"),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["only_right_count"] >= 1
        assert "phash_distance" in body

    def test_rejects_disallowed_extension_on_either_side(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/compare",
            files={
                "file_left": ("document.pdf", b"%PDF-1.4 fake", "application/pdf"),
                "file_right": ("b.jpg", plain_jpeg_bytes, "image/jpeg"),
            },
        )

        assert response.status_code == 400

    def test_rejects_corrupt_image(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/compare",
            files={
                "file_left": ("a.jpg", plain_jpeg_bytes, "image/jpeg"),
                "file_right": ("b.jpg", b"not actually a jpeg", "image/jpeg"),
            },
        )

        assert response.status_code == 422

    def test_missing_one_file_is_rejected(self, client, plain_jpeg_bytes):
        response = client.post(
            "/api/image/compare",
            files={"file_left": ("a.jpg", plain_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 422


class TestStripMetadataEndpoint:
    def test_strips_metadata_and_returns_downloadable_file(self, client, jpeg_with_software_tag):
        response = client.post(
            "/api/image/strip-metadata",
            files={"file": ("photo.jpg", jpeg_with_software_tag, "image/jpeg")},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert "photo_cleaned.jpg" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_location_only_mode_is_accepted(self, client, jpeg_with_gps):
        response = client.post(
            "/api/image/strip-metadata",
            params={"mode": "location_only"},
            files={"file": ("gps.jpg", jpeg_with_gps, "image/jpeg")},
        )

        assert response.status_code == 200

    def test_rejects_disallowed_extension(self, client):
        response = client.post(
            "/api/image/strip-metadata",
            files={"file": ("document.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

        assert response.status_code == 400

    def test_maps_value_error_from_service_to_422(self, client, monkeypatch):
        def fake_strip_metadata(filename, data, mode):
            raise ValueError("Corrupt file")

        monkeypatch.setattr(image_routes, "strip_metadata", fake_strip_metadata)

        response = client.post(
            "/api/image/strip-metadata",
            files={"file": ("photo.jpg", b"\xff\xd8\xff\xd9", "image/jpeg")},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "Corrupt file"
