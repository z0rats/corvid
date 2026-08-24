import json
import subprocess

import pytest

from app.features.image_tools.service import exiftool_service


@pytest.fixture(autouse=True)
def _clear_version_cache():
    exiftool_service.get_exiftool_version.cache_clear()
    yield
    exiftool_service.get_exiftool_version.cache_clear()


class TestAvailability:
    def test_available_when_which_finds_binary(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")
        assert exiftool_service.is_exiftool_available() is True

    def test_unavailable_when_which_returns_none(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: None)
        assert exiftool_service.is_exiftool_available() is False


class TestVersion:
    def test_returns_none_when_not_installed(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: None)
        assert exiftool_service.get_exiftool_version() is None

    def test_returns_stripped_stdout(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")
        monkeypatch.setattr(
            exiftool_service.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="13.30\n", stderr=""),
        )
        assert exiftool_service.get_exiftool_version() == "13.30"

    def test_returns_none_on_subprocess_error(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")

        def fake_run(*_a, **_k):
            raise subprocess.TimeoutExpired(cmd="exiftool", timeout=10)

        monkeypatch.setattr(exiftool_service.subprocess, "run", fake_run)
        assert exiftool_service.get_exiftool_version() is None


class TestExtractExiftoolTags:
    def test_returns_none_when_not_installed(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: None)
        assert exiftool_service.extract_exiftool_tags(b"data") is None

    def test_parses_and_transforms_grouped_keys(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")
        stdout = json.dumps(
            [
                {
                    "SourceFile": "-",
                    "ExifTool:ExifToolVersion": "13.30",
                    "EXIF:DateTimeOriginal": "2024:01:01 12:00:00",
                    "XMP:Title": "My Photo",
                    "File:FileType": "JPEG",
                    "File:FileModifyDate": "2026:08:21 16:39:22+03:00",
                    "File:FilePermissions": "prw-rw----",
                }
            ]
        ).encode("utf-8")
        monkeypatch.setattr(
            exiftool_service.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=stdout, stderr=b""),
        )

        result = exiftool_service.extract_exiftool_tags(b"fake-image-bytes")

        assert result == {
            "EXIF DateTimeOriginal": "2024:01:01 12:00:00",
            "XMP Title": "My Photo",
            "File FileType": "JPEG",
        }
        assert "SourceFile" not in result
        assert "ExifTool ExifToolVersion" not in result
        assert "File FileModifyDate" not in result
        assert "File FilePermissions" not in result

    def test_returns_none_on_invalid_json(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")
        monkeypatch.setattr(
            exiftool_service.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=b"not json", stderr=b""),
        )
        assert exiftool_service.extract_exiftool_tags(b"data") is None

    def test_returns_none_on_subprocess_failure(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")

        def fake_run(*_a, **_k):
            raise subprocess.CalledProcessError(1, "exiftool")

        monkeypatch.setattr(exiftool_service.subprocess, "run", fake_run)
        assert exiftool_service.extract_exiftool_tags(b"data") is None

    def test_returns_none_on_empty_result_array(self, monkeypatch):
        monkeypatch.setattr(exiftool_service.shutil, "which", lambda _: "/usr/bin/exiftool")
        monkeypatch.setattr(
            exiftool_service.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=b"[]", stderr=b""),
        )
        assert exiftool_service.extract_exiftool_tags(b"data") is None
