import os

from app.core.config.settings import settings
from app.core.security.persisted_secret import load_or_create_secret_file


def test_creates_file_with_generated_value_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))

    value, created = load_or_create_secret_file("secret.txt", lambda: "generated-value")

    assert value == "generated-value"
    assert created is True
    assert (tmp_path / "secret.txt").read_text() == "generated-value"


def test_creates_file_with_restrictive_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))

    load_or_create_secret_file("secret.txt", lambda: "generated-value")

    mode = os.stat(tmp_path / "secret.txt").st_mode & 0o777
    assert mode == 0o600


def test_reads_existing_file_without_calling_generator(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    (tmp_path / "secret.txt").write_text("existing-value")

    def _fail():
        raise AssertionError("generator should not be called when file exists")

    value, created = load_or_create_secret_file("secret.txt", _fail)

    assert value == "existing-value"
    assert created is False


def test_strips_whitespace_from_existing_file_contents(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    (tmp_path / "secret.txt").write_text("  value-with-padding  \n")

    value, _ = load_or_create_secret_file("secret.txt", lambda: "unused")

    assert value == "value-with-padding"


def test_creates_data_dir_if_missing(tmp_path, monkeypatch):
    nested = tmp_path / "does" / "not" / "exist"
    monkeypatch.setattr(settings, "data_dir", str(nested))

    value, created = load_or_create_secret_file("secret.txt", lambda: "v")

    assert created is True
    assert nested.is_dir()
    assert value == "v"


def test_concurrent_creation_race_falls_back_to_reading_winners_file(tmp_path, monkeypatch):
    """Simulates another worker creating the file between our exists() check
    and our own os.open(..., O_EXCL) call."""
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    path = tmp_path / "secret.txt"

    def _generator():
        # By the time our generator runs, "another process" has already
        # written the file - our subsequent O_CREAT|O_EXCL open must fail.
        path.write_text("winner-value")
        return "our-value"

    value, created = load_or_create_secret_file("secret.txt", _generator)

    assert value == "winner-value"
    assert created is False
