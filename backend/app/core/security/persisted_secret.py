"""Shared helper for secrets that are generated once and persisted to a file
under <data_dir> so they survive restarts (e.g. the encryption key in
secrets_crypto.py, the API access token in access_control.py).
"""

import contextlib
import os

from app.core.config.settings import settings


def load_or_create_secret_file(filename: str, generator) -> tuple[str, bool]:
    """Return (secret_value, was_just_created) for `<data_dir>/<filename>`.

    Creates the file (mode 0600) via `generator()` if it doesn't exist yet.
    """
    path = os.path.join(settings.data_dir, filename)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip(), False

    os.makedirs(settings.data_dir, exist_ok=True)
    value = generator()
    try:
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    except FileExistsError:
        # Another worker created it between our exists() check and open() - use theirs.
        with open(path) as f:
            return f.read().strip(), False
    with os.fdopen(fd, "w") as f:
        f.write(value)
    return value, True


def overwrite_secret_file(filename: str, value: str) -> None:
    """Replace `<data_dir>/<filename>` with `value` (mode 0600), for rotating a
    secret that was previously created via `load_or_create_secret_file`.

    Writes to a temp file in the same directory and `os.replace`s it into place
    so a concurrent reader never observes a partially-written file.
    """
    path = os.path.join(settings.data_dir, filename)
    tmp_path = f"{path}.tmp-{os.getpid()}"
    fd = os.open(tmp_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(value)
        os.replace(tmp_path, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_path)
        raise
