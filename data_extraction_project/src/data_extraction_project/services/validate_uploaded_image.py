
from data_extraction_project.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    InvalidTextFileError
)

from collections.abc import Collection
from pathlib import Path

def _check_upload(
    filename: str, content: bytes, allowed_exts: Collection[str], max_bytes: int
) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_exts:
        raise UnsupportedFileTypeError(
            suffix=suffix or "(none)", allowed=", ".join(sorted(allowed_exts))
        )
    if not content:
        raise EmptyFileError()
    if len(content) > max_bytes:
        raise FileTooLargeError(max_mb=f"{max_bytes / 1_048_576:g}")
    return suffix


def validate_image_upload(
    filename: str,
    content: bytes,
    allowed_mime_types: dict[str, str],
    max_bytes: int,
) -> str:
    """Validate an uploaded image and return its MIME type (derived from the extension,
    not the client-supplied content type)."""
    suffix = _check_upload(filename, content, allowed_mime_types, max_bytes)
    return allowed_mime_types[suffix]


def validate_text_upload(
    filename: str,
    content: bytes,
    allowed_exts: Collection[str],
    max_bytes: int,
) -> str:
    """Validate an uploaded text file and return its decoded contents."""
    _check_upload(filename, content, allowed_exts, max_bytes)
    try:
        text = content.decode("utf-8-sig")  # also strips a BOM if present
    except UnicodeDecodeError as exc:
        raise InvalidTextFileError() from exc
    if not text.strip():
        raise EmptyFileError()
    return text