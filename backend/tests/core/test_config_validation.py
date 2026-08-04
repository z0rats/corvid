from app.core.config import validation
from app.core.config.settings import settings

# --- validate_directory_exists ----------------------------------------------


def test_validate_directory_exists_true_for_existing_directory(tmp_path):
    assert validation.validate_directory_exists(str(tmp_path)) is True


def test_validate_directory_exists_creates_missing_directory_by_default(tmp_path):
    target = tmp_path / "new" / "nested"
    assert validation.validate_directory_exists(str(target)) is True
    assert target.is_dir()


def test_validate_directory_exists_returns_false_when_create_disabled(tmp_path):
    target = tmp_path / "missing"
    assert validation.validate_directory_exists(str(target), create_if_missing=False) is False
    assert not target.exists()


def test_validate_directory_exists_returns_false_when_path_is_a_file(tmp_path):
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("x")

    assert validation.validate_directory_exists(str(file_path), create_if_missing=False) is False


# --- validate_database_settings ---------------------------------------------


def test_validate_database_settings_flags_missing_url(monkeypatch):
    monkeypatch.setattr(settings.database, "url", "")
    errors = validation.validate_database_settings()
    assert "Database URL is not configured" in errors


def test_validate_database_settings_flags_non_positive_pool_size(monkeypatch):
    monkeypatch.setattr(settings.database, "pool_size", 0)
    errors = validation.validate_database_settings()
    assert "Database pool size must be greater than 0" in errors


def test_validate_database_settings_flags_negative_max_overflow(monkeypatch):
    monkeypatch.setattr(settings.database, "max_overflow", -1)
    errors = validation.validate_database_settings()
    assert "Database max overflow cannot be negative" in errors


def test_validate_database_settings_flags_missing_sqlite_directory(monkeypatch, tmp_path):
    missing_dir = tmp_path / "does_not_exist_yet"
    monkeypatch.setattr(settings.database, "url", f"sqlite:///{missing_dir}/corvid.db")

    errors = validation.validate_database_settings()

    # validate_directory_exists auto-creates by default, so this should NOT
    # produce an error, and should have created the directory as a side effect.
    assert errors == []
    assert missing_dir.is_dir()


def test_validate_database_settings_passes_for_valid_config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings.database, "url", f"sqlite:///{tmp_path}/corvid.db")
    monkeypatch.setattr(settings.database, "pool_size", 10)
    monkeypatch.setattr(settings.database, "max_overflow", 20)

    assert validation.validate_database_settings() == []


# --- validate_logging_settings ----------------------------------------------


def test_validate_logging_settings_flags_invalid_level(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.logging, "level", "NOTALEVEL")
    monkeypatch.setattr(settings.logging, "dir", str(tmp_path))

    errors = validation.validate_logging_settings()

    assert any("Invalid logging level" in e for e in errors)


def test_validate_logging_settings_accepts_lowercase_valid_level(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.logging, "level", "debug")
    monkeypatch.setattr(settings.logging, "dir", str(tmp_path))
    monkeypatch.setattr(settings.logging, "max_file_size", 1024)
    monkeypatch.setattr(settings.logging, "backup_count", 1)

    assert validation.validate_logging_settings() == []


def test_validate_logging_settings_flags_non_positive_max_file_size(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.logging, "dir", str(tmp_path))
    monkeypatch.setattr(settings.logging, "max_file_size", 0)

    errors = validation.validate_logging_settings()

    assert "Log file max size must be greater than 0" in errors


def test_validate_logging_settings_flags_negative_backup_count(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.logging, "dir", str(tmp_path))
    monkeypatch.setattr(settings.logging, "backup_count", -1)

    errors = validation.validate_logging_settings()

    assert "Log backup count cannot be negative" in errors


# --- validate_api_settings --------------------------------------------------


def test_validate_api_settings_flags_missing_title_and_version(monkeypatch):
    monkeypatch.setattr(settings.api, "title", "")
    monkeypatch.setattr(settings.api, "version", "")

    errors = validation.validate_api_settings()

    assert "API title is not configured" in errors
    assert "API version is not configured" in errors


def test_validate_api_settings_flags_non_list_cors_origins(monkeypatch):
    monkeypatch.setattr(settings.api, "cors_origins", "http://localhost:3000")

    errors = validation.validate_api_settings()

    assert "CORS origins must be a list" in errors


def test_validate_api_settings_passes_for_valid_config(monkeypatch):
    monkeypatch.setattr(settings.api, "title", "Corvid")
    monkeypatch.setattr(settings.api, "version", "1.0.0")
    monkeypatch.setattr(settings.api, "cors_origins", ["http://localhost:3000"])

    assert validation.validate_api_settings() == []


# --- validate_environment_variables -----------------------------------------


def test_validate_environment_variables_skips_checks_outside_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings.api, "debug", True)

    assert validation.validate_environment_variables() == []


def test_validate_environment_variables_flags_debug_enabled_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings.api, "debug", True)
    monkeypatch.setattr(settings.api, "cors_origins", ["https://corvid.example"])
    monkeypatch.setattr(settings.api, "trusted_hosts", ["corvid.example"])

    errors = validation.validate_environment_variables()

    assert "Debug mode should be disabled in production" in errors


def test_validate_environment_variables_flags_wildcard_cors_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings.api, "debug", False)
    monkeypatch.setattr(settings.api, "cors_origins", ["*"])
    monkeypatch.setattr(settings.api, "trusted_hosts", ["corvid.example"])

    errors = validation.validate_environment_variables()

    assert "CORS origins should be restricted in production" in errors


def test_validate_environment_variables_flags_default_cors_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings.api, "debug", False)
    monkeypatch.setattr(settings.api, "cors_origins", ["http://localhost:3000"])
    monkeypatch.setattr(settings.api, "trusted_hosts", ["corvid.example"])

    errors = validation.validate_environment_variables()

    assert any("localhost development default" in e and "CORS" in e for e in errors)


def test_validate_environment_variables_flags_default_trusted_hosts_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings.api, "debug", False)
    monkeypatch.setattr(settings.api, "cors_origins", ["https://corvid.example"])
    monkeypatch.setattr(settings.api, "trusted_hosts", ["localhost", "127.0.0.1"])

    errors = validation.validate_environment_variables()

    assert any("Trusted hosts" in e for e in errors)


def test_validate_environment_variables_passes_for_properly_configured_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings.api, "debug", False)
    monkeypatch.setattr(settings.api, "cors_origins", ["https://corvid.example"])
    monkeypatch.setattr(settings.api, "trusted_hosts", ["corvid.example"])

    assert validation.validate_environment_variables() == []


# --- validate_security_settings ---------------------------------------------


def test_validate_security_settings_flags_private_network_targets_allowed(monkeypatch):
    monkeypatch.setattr(settings.security, "allow_private_network_targets", True)

    errors = validation.validate_security_settings()

    assert len(errors) == 1
    assert "SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS" in errors[0]


def test_validate_security_settings_passes_by_default(monkeypatch):
    monkeypatch.setattr(settings.security, "allow_private_network_targets", False)
    assert validation.validate_security_settings() == []


# --- validate_all_settings / get_validation_summary / log_validation_results


def test_validate_all_settings_returns_one_key_per_category(monkeypatch, tmp_path):
    _make_all_valid(monkeypatch, tmp_path)

    results = validation.validate_all_settings()

    assert set(results.keys()) == {"database", "logging", "api", "environment", "security"}


def test_get_validation_summary_valid_when_no_errors(monkeypatch, tmp_path):
    _make_all_valid(monkeypatch, tmp_path)

    summary = validation.get_validation_summary()

    assert summary["valid"] is True
    assert summary["total_errors"] == 0
    assert "passed" in summary["summary"]


def test_get_validation_summary_invalid_when_errors_present(monkeypatch, tmp_path):
    _make_all_valid(monkeypatch, tmp_path)
    monkeypatch.setattr(settings.database, "pool_size", 0)

    summary = validation.get_validation_summary()

    assert summary["valid"] is False
    assert summary["total_errors"] == 1
    assert "failed" in summary["summary"]


def test_log_validation_results_does_not_raise(monkeypatch, tmp_path):
    _make_all_valid(monkeypatch, tmp_path)
    validation.log_validation_results()


def test_log_validation_results_does_not_raise_with_errors(monkeypatch, tmp_path):
    _make_all_valid(monkeypatch, tmp_path)
    monkeypatch.setattr(settings.database, "pool_size", 0)
    validation.log_validation_results()


# --- ensure_required_directories --------------------------------------------


def test_ensure_required_directories_creates_all_configured_directories(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    static_dir = tmp_path / "static"

    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings.logging, "dir", str(log_dir))
    monkeypatch.setattr(settings, "static_dir", str(static_dir))

    validation.ensure_required_directories()

    assert data_dir.is_dir()
    assert log_dir.is_dir()
    assert static_dir.is_dir()


def _make_all_valid(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.database, "url", f"sqlite:///{tmp_path}/corvid.db")
    monkeypatch.setattr(settings.database, "pool_size", 10)
    monkeypatch.setattr(settings.database, "max_overflow", 20)
    monkeypatch.setattr(settings.logging, "level", "INFO")
    monkeypatch.setattr(settings.logging, "dir", str(tmp_path / "logs"))
    monkeypatch.setattr(settings.logging, "max_file_size", 1024)
    monkeypatch.setattr(settings.logging, "backup_count", 1)
    monkeypatch.setattr(settings.api, "title", "Corvid")
    monkeypatch.setattr(settings.api, "version", "1.0.0")
    monkeypatch.setattr(settings.api, "cors_origins", ["https://corvid.example"])
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings.security, "allow_private_network_targets", False)
