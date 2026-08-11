"""Exercises `file_upload.py`, the shared read-validate-dispatch skeleton used by
every upload endpoint in `image_tools`/`email_analyzer`. `validate_uploaded_file`
is tested against a minimal duck-typed stand-in for `UploadFile` (only `.filename`
and `.read()` are used); `run_file_endpoint` is tested against plain sync/async
callables so the dispatch/error-mapping logic runs independent of any real service.
"""
import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.core.utils.file_upload import run_file_endpoint, validate_uploaded_file


class FakeUploadFile:
    def __init__(self, filename: str | None, content: bytes = b"data", read_error: Exception | None = None):
        self.filename = filename
        self._content = content
        self._read_error = read_error

    async def read(self) -> bytes:
        if self._read_error:
            raise self._read_error
        return self._content


def _run(coro):
    return asyncio.run(coro)


def _always_valid(filename: str, size: int) -> tuple[bool, str | None, str | None]:
    return True, None, None


def _always_invalid(filename: str, size: int) -> tuple[bool, str | None, str | None]:
    return False, "SOME_VALIDATION_ERROR", "invalid file"


# --- validate_uploaded_file --------------------------------------------------


def test_validate_uploaded_file_rejects_missing_filename():
    file = FakeUploadFile(filename=None)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(
            validate_uploaded_file(
                file, no_file_code="NO_FILE", read_error_code="READ_ERROR", validate_fn=_always_valid
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "NO_FILE"


def test_validate_uploaded_file_maps_read_failure():
    file = FakeUploadFile(filename="a.txt", read_error=RuntimeError("boom"))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(
            validate_uploaded_file(
                file, no_file_code="NO_FILE", read_error_code="READ_ERROR", validate_fn=_always_valid
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "READ_ERROR"


def test_validate_uploaded_file_propagates_validate_fn_failure():
    file = FakeUploadFile(filename="a.txt")

    with pytest.raises(AppHTTPException) as exc_info:
        _run(
            validate_uploaded_file(
                file, no_file_code="NO_FILE", read_error_code="READ_ERROR", validate_fn=_always_invalid
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "SOME_VALIDATION_ERROR"
    assert exc_info.value.detail == "invalid file"


def test_validate_uploaded_file_returns_bytes_on_success():
    file = FakeUploadFile(filename="a.txt", content=b"hello world")

    result = _run(
        validate_uploaded_file(file, no_file_code="NO_FILE", read_error_code="READ_ERROR", validate_fn=_always_valid)
    )

    assert result == b"hello world"


# --- run_file_endpoint -------------------------------------------------------


def _sync_ok(a, b):
    return a + b


def _sync_value_error(*_args):
    raise ValueError("bad input")


def _sync_boom(*_args):
    raise RuntimeError("kaboom")


async def _async_ok(a, b):
    return a + b


def test_run_file_endpoint_returns_result_on_success():
    result = _run(
        run_file_endpoint(_sync_ok, 1, 2, error_code="FAILED", failure_message="failed")
    )

    assert result == 3


def test_run_file_endpoint_maps_value_error_to_own_message_and_error_code():
    with pytest.raises(AppHTTPException) as exc_info:
        _run(
            run_file_endpoint(
                _sync_value_error,
                "x",
                error_code="FAILED",
                failure_message="failed",
                value_error_code="SPECIFIC_CODE",
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "SPECIFIC_CODE"
    assert exc_info.value.detail == "bad input"


def test_run_file_endpoint_value_error_reuses_error_code_when_unset():
    with pytest.raises(AppHTTPException) as exc_info:
        _run(run_file_endpoint(_sync_value_error, "x", error_code="FAILED", failure_message="failed"))

    assert exc_info.value.error_code == "FAILED"


def test_run_file_endpoint_maps_generic_exception_to_error_code():
    with pytest.raises(AppHTTPException) as exc_info:
        _run(run_file_endpoint(_sync_boom, "x", error_code="FAILED", failure_message="operation failed"))

    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "FAILED"


def test_run_file_endpoint_runs_coroutine_function_directly_when_not_in_thread():
    result = _run(
        run_file_endpoint(_async_ok, 2, 3, error_code="FAILED", failure_message="failed", run_in_thread=False)
    )

    assert result == 5
