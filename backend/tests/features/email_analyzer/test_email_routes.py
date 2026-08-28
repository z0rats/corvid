from email.message import EmailMessage

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.exceptions import register_exception_handlers
from app.features.email_analyzer.routers import email_routes


def _sample_eml_bytes() -> bytes:
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.org"
    msg["Subject"] = "Meeting notes"
    msg.set_content("hello there")
    return msg.as_bytes()


@pytest.fixture
def client():
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(email_routes.router)
    return TestClient(app)


class TestAnalyzeEmailFile:
    def test_analyzes_a_valid_eml_upload(self, client):
        response = client.post(
            "/api/email/analyze",
            files={"file": ("sample.eml", _sample_eml_bytes(), "message/rfc822")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["basic_info"]["from"] == "alice@example.com"
        assert body["file_size"] == len(_sample_eml_bytes())

    def test_rejects_a_disallowed_extension_with_400(self, client):
        response = client.post(
            "/api/email/analyze",
            files={"file": ("sample.pdf", b"not an email", "application/pdf")},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "EMAIL_INVALID_FILE_TYPE"

    def test_rejects_an_empty_file_with_400(self, client):
        response = client.post(
            "/api/email/analyze",
            files={"file": ("sample.eml", b"", "message/rfc822")},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "EMAIL_FILE_EMPTY"

    def test_maps_an_analysis_failure_to_422(self, client, monkeypatch):
        def fake_analyze(_data):
            raise ValueError("could not parse")

        monkeypatch.setattr(email_routes, "analyze_email_content", fake_analyze)

        response = client.post(
            "/api/email/analyze",
            files={"file": ("sample.eml", _sample_eml_bytes(), "message/rfc822")},
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "EMAIL_ANALYSIS_FAILED"


class TestAiAnalyzeEmailBody:
    def test_delegates_to_the_ai_service_and_wraps_the_result(self, client, monkeypatch):
        async def fake_analyze_email_body(email_body, db):
            assert email_body == "please analyze this"
            return {"verdict": "suspicious"}

        monkeypatch.setattr(email_routes, "analyze_email_body", fake_analyze_email_body)

        response = client.post("/api/email/ai-analysis", json={"input": "please analyze this"})

        assert response.status_code == 200
        assert response.json() == {"analysis_result": {"verdict": "suspicious"}}

    def test_maps_a_value_error_from_the_service_to_422(self, client, monkeypatch):
        async def fake_analyze_email_body(email_body, db):
            raise ValueError("no LLM configured")

        monkeypatch.setattr(email_routes, "analyze_email_body", fake_analyze_email_body)

        response = client.post("/api/email/ai-analysis", json={"input": "text"})

        assert response.status_code == 422
        assert response.json()["error_code"] == "EMAIL_AI_ANALYSIS_FAILED"

    def test_rejects_empty_input_with_422(self, client):
        response = client.post("/api/email/ai-analysis", json={"input": ""})
        assert response.status_code == 422


class TestExportAnalysisReport:
    def _minimal_result(self):
        return {
            "basic_info": {},
            "headers": [],
            "eml_hashes": {"md5": "d" * 32, "sha1": "d" * 40, "sha256": "d" * 64},
        }

    def test_returns_the_generated_report_with_a_content_disposition_header(
        self, client, monkeypatch
    ):
        def fake_generate_analysis_report(result, format, locale):
            assert format == "html"
            assert locale == "en"
            return b"<html>report</html>", "text/html", "report.html"

        monkeypatch.setattr(email_routes, "generate_analysis_report", fake_generate_analysis_report)

        response = client.post("/api/email/report", json=self._minimal_result())

        assert response.status_code == 200
        assert response.content == b"<html>report</html>"
        assert response.headers["content-type"].startswith("text/html")
        assert 'filename="report.html"' in response.headers["content-disposition"]

    def test_passes_through_the_format_and_locale_query_params(self, client, monkeypatch):
        def fake_generate_analysis_report(result, format, locale):
            assert format == "pdf"
            assert locale == "ru"
            return b"%PDF-1.4", "application/pdf", "report.pdf"

        monkeypatch.setattr(email_routes, "generate_analysis_report", fake_generate_analysis_report)

        response = client.post(
            "/api/email/report",
            params={"format": "pdf", "locale": "ru"},
            json=self._minimal_result(),
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestHealthCheck:
    def test_reports_service_metadata(self, client):
        response = client.get("/api/email/health")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "email_analyzer"
        assert body["status"] == "healthy"
        assert ".eml" in body["supported_formats"]
