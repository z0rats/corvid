"""HTTP surface of the IOC extractor: file upload (extension/size gate,
multi-encoding decode) and plain-text extraction, plus error mapping."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import register_exception_handlers
from app.features.ioc_tools.ioc_extractor.routers import internal_ioc_extractor_routes as routes
from app.features.ioc_tools.ioc_extractor.utils import validation_utils as vu

SAMPLE = (
    "C2 at 45.33.32.156 and evil-domain.com, hash d41d8cd98f00b204e9800998ecf8427e, CVE-2024-3094"
)


@pytest.fixture
def client():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(routes.router)
    return TestClient(app, raise_server_exceptions=False)


def _upload(client, name, data):
    return client.post("/api/extractor/", files={"file": (name, data, "text/plain")})


class TestFileUpload:
    def test_extracts_iocs_from_utf8_file(self, client):
        r = _upload(client, "report.txt", SAMPLE.encode())
        assert r.status_code == 200
        body = r.json()
        assert "45.33.32.156" in body["ips"]
        assert "d41d8cd98f00b204e9800998ecf8427e" in body["md5"]
        assert "CVE-2024-3094" in body["cves"]

    def test_non_utf8_file_falls_back_to_another_encoding(self, client):
        data = ("Café report: " + SAMPLE).encode("cp1252")
        r = _upload(client, "report.log", data)
        assert r.status_code == 200
        assert "45.33.32.156" in r.json()["ips"]

    @pytest.mark.parametrize("name", ["malware.exe", "doc.pdf", "noext", "archive.txt.zip"])
    def test_unsupported_extension_rejected(self, client, name):
        r = _upload(client, name, b"1.2.3.4")
        assert r.status_code == 400
        assert r.json()["error_code"] == "EXTRACTOR_FILE_VALIDATION_ERROR"

    def test_file_over_size_limit_rejected(self, client, monkeypatch):
        monkeypatch.setattr(vu, "MAX_FILE_SIZE", 10)
        r = _upload(client, "big.txt", b"x" * 11)
        assert r.status_code == 400
        assert "too large" in r.json()["detail"]

    def test_service_value_error_maps_to_400(self, client, monkeypatch):
        def boom(*a):
            raise ValueError("empty after sanitizing")

        monkeypatch.setattr(routes, "extract_iocs_from_file_content", boom)
        r = _upload(client, "a.txt", b"abc")
        assert r.status_code == 400
        assert r.json()["error_code"] == "EXTRACTOR_FILE_PROCESSING_ERROR"

    def test_unexpected_error_maps_to_500_without_leaking_text(self, client, monkeypatch):
        def boom(*a):
            raise KeyError("internal secret detail")

        monkeypatch.setattr(routes, "extract_iocs_from_file_content", boom)
        r = _upload(client, "a.txt", b"abc")
        assert r.status_code == 500
        assert r.json()["error_code"] == "EXTRACTOR_UNEXPECTED_ERROR"
        assert "secret" not in r.text


class TestTextExtraction:
    def test_extracts_from_text(self, client):
        r = client.post("/api/extractor/text/", json={"text": SAMPLE})
        assert r.status_code == 200
        assert "45.33.32.156" in r.json()["ips"]

    @pytest.mark.parametrize("text", ["", "   \n\t "])
    def test_empty_or_whitespace_text_rejected(self, client, text):
        assert client.post("/api/extractor/text/", json={"text": text}).status_code == 422

    @pytest.mark.parametrize(
        ("exc", "status", "code"),
        [
            (ValueError("bad"), 400, "EXTRACTOR_TEXT_VALIDATION_ERROR"),
            (RuntimeError("pattern failure"), 500, "EXTRACTOR_TEXT_PROCESSING_FAILED"),
            (KeyError("x"), 500, "EXTRACTOR_TEXT_UNEXPECTED_ERROR"),
        ],
    )
    def test_error_mapping(self, client, monkeypatch, exc, status, code):
        def boom(text):
            raise exc

        monkeypatch.setattr(routes, "extract_iocs", boom)
        r = client.post("/api/extractor/text/", json={"text": "1.2.3.4"})
        assert r.status_code == status
        assert r.json()["error_code"] == code


class TestValidationUtils:
    @pytest.mark.parametrize(
        ("name", "ext"),
        [("a.TXT", ".txt"), ("x.tar.gz", ".gz"), ("noext", ""), ("", ""), (".env", ".env")],
    )
    def test_get_file_extension(self, name, ext):
        assert vu.get_file_extension(name) == ext

    def test_validate_text_content(self):
        assert vu.validate_text_content("1.2.3.4") is True
        assert vu.validate_text_content("ab") is False
        assert vu.validate_text_content("   ") is False
        assert vu.validate_text_content(None) is False
        assert vu.validate_text_content("\x00\x01\x02\x03\x04ab") is False

    def test_sanitize_text_content_normalizes_and_strips_control_chars(self):
        raw = "a\r\nb\rc\n\n\n\n\n\nd   \t  e\x00\x07f"
        assert vu.sanitize_text_content(raw) == "a\nb\nc\n\n\nd  ef"
        assert vu.sanitize_text_content("") == ""

    def test_decode_prefers_utf8(self):
        assert vu.decode_file_content("ü".encode()) == ("ü", "utf-8")
        text, enc = vu.decode_file_content(b"\xfc")
        assert enc == "latin-1"
        assert text == "ü"

    def test_extraction_patterns_compile(self):
        assert vu.validate_extraction_patterns() is True

    def test_estimate_processing_time_has_floor_and_capped_overhead(self):
        assert vu.estimate_processing_time(0) == 0.1
        assert vu.estimate_processing_time(10_000_000) == pytest.approx(10_000 + 5.0)
