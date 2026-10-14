from pathlib import Path

from data_extraction_project.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)


def validate_image_upload(
    filename: str,
    content: bytes,
    allowed_mime_types: dict[str, str],
    max_bytes: int,
) -> str:
    """Validate an uploaded image and return its MIME type (derived from the extension,
    not the client-supplied content type)."""
    suffix = Path(filename).suffix.lower()
    mime_type = allowed_mime_types.get(suffix)
    if mime_type is None:
        raise UnsupportedFileTypeError(
            suffix=suffix or "(none)",
            allowed=", ".join(sorted(allowed_mime_types)),
        )
    if not content:
        raise EmptyFileError()
    if len(content) > max_bytes:
        raise FileTooLargeError(max_mb=f"{max_bytes / 1_048_576:g}")
    return mime_type