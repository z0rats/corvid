import logging
import os
import pickle
import tempfile

from maigret.report import (
    generate_report_context,
    save_csv_report,
    save_html_report,
    save_json_report,
    save_pdf_report,
    save_txt_report,
    save_xmind_report,
)

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(settings.data_dir, "username_search_reports")

# format -> (media type, file extension)
EXPORT_FORMATS: dict[str, tuple[str, str]] = {
    "csv": ("text/csv", ".csv"),
    "txt": ("text/plain", ".txt"),
    "json": ("application/json", ".json"),
    "html": ("text/html", ".html"),
    "pdf": ("application/pdf", ".pdf"),
    "xmind": ("application/octet-stream", ".xmind"),
}


def _results_path(search_id: int) -> str:
    # int() re-validates at the boundary rather than trusting the type hint, so this
    # can never format anything but digits into the filename (no path traversal).
    return os.path.join(REPORTS_DIR, f"{int(search_id)}.pkl")


def save_scan_results(search_id: int, results: dict) -> None:
    """Persist the full (found + not-found) raw scan results to disk for later export.

    Not stored in the DB - thousands of not-found rows per run aren't useful
    to query, but full results are needed for faithful CSV/TXT export (which
    list every checked site, not just found ones, matching Maigret's own
    report format). Pickled rather than JSON-encoded since results contain
    non-trivially-serializable objects (MaigretCheckResult, enums); this is
    a private on-disk artifact written and read only by this same process,
    never by untrusted input.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(_results_path(search_id), "wb") as f:
        pickle.dump(results, f)


def has_scan_results(search_id: int) -> bool:
    return os.path.isfile(_results_path(search_id))


def load_scan_results(search_id: int) -> dict | None:
    path = _results_path(search_id)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def delete_scan_results(search_id: int) -> None:
    path = _results_path(search_id)
    if os.path.isfile(path):
        os.remove(path)


def generate_export(search_id: int, username: str, results: dict, fmt: str) -> tuple[bytes, str, str]:
    """Generate a report file in the given format, reusing Maigret's own report
    generators (maigret.report) directly rather than reimplementing export logic.

    Returns (content, media_type, filename).
    """
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}")

    media_type, ext = EXPORT_FORMATS[fmt]
    filename = f"username-search-{search_id}-{username}{ext}"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if fmt == "csv":
            save_csv_report(tmp_path, username, results)
        elif fmt == "txt":
            save_txt_report(tmp_path, username, results)
        elif fmt == "json":
            save_json_report(tmp_path, username, results, report_type="simple")
        elif fmt == "xmind":
            save_xmind_report(tmp_path, username, results)
        else:  # html, pdf
            context = generate_report_context([(username, "username", results)])
            if fmt == "html":
                save_html_report(tmp_path, context)
            else:
                save_pdf_report(tmp_path, context)

        with open(tmp_path, "rb") as f:
            content = f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return content, media_type, filename
