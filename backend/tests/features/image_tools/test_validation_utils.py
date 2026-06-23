from app.features.image_tools.config.image_config import MAX_FILE_SIZE_BYTES
from app.features.image_tools.utils.validation_utils import validate_file_upload


def test_valid_upload_passes():
    is_valid, error = validate_file_upload('photo.jpg', 1024)

    assert is_valid is True
    assert error is None


def test_missing_filename_is_rejected():
    is_valid, error = validate_file_upload(None, 1024)

    assert is_valid is False
    assert 'No filename' in error


def test_disallowed_extension_is_rejected():
    is_valid, error = validate_file_upload('document.pdf', 1024)

    assert is_valid is False
    assert 'Invalid file type' in error


def test_oversized_file_is_rejected():
    is_valid, error = validate_file_upload('photo.jpg', MAX_FILE_SIZE_BYTES + 1)

    assert is_valid is False
    assert 'too large' in error


def test_empty_file_is_rejected():
    is_valid, error = validate_file_upload('photo.jpg', 0)

    assert is_valid is False
    assert 'empty' in error


def test_extension_check_is_case_insensitive():
    is_valid, error = validate_file_upload('PHOTO.JPG', 1024)

    assert is_valid is True
    assert error is None
