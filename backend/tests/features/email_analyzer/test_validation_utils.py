from datetime import datetime, timedelta, timezone

from app.features.email_analyzer.utils.validation_utils import (
    sanitize_filename,
    validate_email_date,
    validate_file_upload,
    validate_hash_algorithm,
)

# --- validate_file_upload ---------------------------------------------------


def test_validate_file_upload_rejects_missing_filename():
    is_valid, code, message = validate_file_upload(None, 100)
    assert is_valid is False
    assert code == "EMAIL_NO_FILENAME"
    assert message


def test_validate_file_upload_rejects_disallowed_extension():
    is_valid, code, _ = validate_file_upload("malware.exe", 100)
    assert is_valid is False
    assert code == "EMAIL_INVALID_FILE_TYPE"


def test_validate_file_upload_accepts_allowed_extension_case_insensitively():
    is_valid, code, message = validate_file_upload("Sample.EML", 100)
    assert is_valid is True
    assert code is None
    assert message is None


def test_validate_file_upload_rejects_file_too_large():
    is_valid, code, _ = validate_file_upload("sample.eml", 51 * 1024 * 1024)
    assert is_valid is False
    assert code == "EMAIL_FILE_TOO_LARGE"


def test_validate_file_upload_rejects_empty_file():
    is_valid, code, _ = validate_file_upload("sample.eml", 0)
    assert is_valid is False
    assert code == "EMAIL_FILE_EMPTY"


def test_validate_file_upload_accepts_valid_file():
    assert validate_file_upload("sample.eml", 1024) == (True, None, None)


# --- validate_email_date ----------------------------------------------------


def test_validate_email_date_accepts_missing_header():
    assert validate_email_date(None) == (True, None)


def test_validate_email_date_accepts_recent_date():
    recent = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S %z")
    is_valid, message = validate_email_date(recent)
    assert is_valid is True
    assert message is None


def test_validate_email_date_rejects_future_date():
    future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S %z")
    is_valid, message = validate_email_date(future)
    assert is_valid is False
    assert "future date" in message


def test_validate_email_date_rejects_date_older_than_max_age():
    old = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%a, %d %b %Y %H:%M:%S %z")
    is_valid, message = validate_email_date(old)
    assert is_valid is False
    assert "days old" in message


def test_validate_email_date_rejects_unparseable_date():
    is_valid, message = validate_email_date("not a date")
    assert is_valid is False
    assert "invalid date format" in message


# --- validate_hash_algorithm -------------------------------------------------


def test_validate_hash_algorithm_accepts_supported_algorithms():
    assert validate_hash_algorithm("md5") is True
    assert validate_hash_algorithm("sha1") is True
    assert validate_hash_algorithm("sha256") is True


def test_validate_hash_algorithm_rejects_unsupported_algorithm():
    assert validate_hash_algorithm("sha512") is False
    assert validate_hash_algorithm("") is False


# --- sanitize_filename -------------------------------------------------------


def test_sanitize_filename_replaces_unsafe_characters():
    assert sanitize_filename('a<b>c:d"e/f\\g|h?i*j.txt') == "a_b_c_d_e_f_g_h_i_j.txt"


def test_sanitize_filename_returns_unknown_for_empty_input():
    assert sanitize_filename("") == "unknown"
    assert sanitize_filename(None) == "unknown"


def test_sanitize_filename_truncates_overly_long_names_preserving_extension():
    long_name = ("a" * 300) + ".txt"
    sanitized = sanitize_filename(long_name)

    assert len(sanitized) <= 255
    assert sanitized.endswith(".txt")


def test_sanitize_filename_truncates_overly_long_name_without_extension():
    long_name = "a" * 300
    sanitized = sanitize_filename(long_name)

    assert len(sanitized) == 250
