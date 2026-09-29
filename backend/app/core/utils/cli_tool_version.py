"""Shared helper for reading an installed CLI tool's version via a `-version`-style
flag, for tools that aren't a pip package (so `pypi_version_check.py`'s
PyPI-latest-version check doesn't apply to them - see AGENTS.md's
external-tool-version-exposure convention). Used by `subfinder_service.py` and
`host_probe_service.py`, both projectdiscovery Go binaries that print
"Current Version: vX.Y.Z" via the same shared `updateutils` banner code - hence
the one default regex below.
"""

import logging
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)

DEFAULT_VERSION_REGEX = re.compile(r"Current Version:\s*(\S+)")
VERSION_TIMEOUT_SECONDS = 10


def is_binary_available(binary_name: str) -> bool:
    return shutil.which(binary_name) is not None


def get_cli_tool_version(
    binary_name: str,
    *,
    version_args: tuple[str, ...] = ("-version", "-duc"),
    version_regex: re.Pattern[str] = DEFAULT_VERSION_REGEX,
) -> str | None:
    """Return `binary_name`'s installed version, or None if it's not installed or
    the version output couldn't be parsed. Never raises."""
    if not is_binary_available(binary_name):
        return None
    try:
        result = subprocess.run(
            [binary_name, *version_args],
            capture_output=True,
            text=True,
            timeout=VERSION_TIMEOUT_SECONDS,
        )
        match = version_regex.search(result.stdout + result.stderr)
        return match.group(1) if match else None
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning("Error reading %s version: %s", binary_name, e)
        return None
