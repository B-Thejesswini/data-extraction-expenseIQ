
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
    """Run the checks common to every upload and return the lowercased extension.

    Checks run in order: extension, then empty content, then size. Only the file name
    and byte length are inspected, so a file with a valid extension can still hold the
    wrong kind of data. Callers are responsible for checking the contents.

    Args:
        filename: Original upload name, used only for its extension.
        content: Raw file bytes.
        allowed_exts: Accepted extensions, lowercase and including the dot (for
            example `.png`). A dict is accepted, in which case its keys are used.
        max_bytes: Largest accepted file size, in bytes.

    Returns:
        The file's extension in lowercase, for example `.png`.

    Raises:
        UnsupportedFileTypeError: Extension is missing or not in `allowed_exts`.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_bytes`.
    """

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
    """Validate an uploaded image and return its MIME type.

    The MIME type is looked up from the file extension, not taken from the
    client-supplied content type, since the client controls the latter. The image
    data itself is not inspected.

    Args:
        filename: Original upload name, used to determine the image type.
        content: Raw image bytes.
        allowed_mime_types: Map of accepted extensions to their MIME types, such as
            `{".png": "image/png"}`.
        max_bytes: Largest accepted file size, in bytes.

    Returns:
        The MIME type matching the file's extension.

    Raises:
        UnsupportedFileTypeError: Extension is missing or not in `allowed_mime_types`.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_bytes`.
    """
    suffix = _check_upload(filename, content, allowed_mime_types, max_bytes)
    return allowed_mime_types[suffix]


def validate_text_upload(
    filename: str,
    content: bytes,
    allowed_exts: Collection[str],
    max_bytes: int,
) -> str:
    """Validate an uploaded text file and return its decoded contents.

    Decodes as UTF-8 and strips a leading BOM if present.

    Args:
        filename: Original upload name, used to check the extension.
        content: Raw file bytes.
        allowed_exts: Accepted extensions, lowercase and including the dot (for
            example `.md`).
        max_bytes: Largest accepted file size, in bytes.

    Returns:
        The decoded text of the file.

    Raises:
        UnsupportedFileTypeError: Extension is missing or not in `allowed_exts`.
        EmptyFileError: The file has no content, or only whitespace once decoded.
        FileTooLargeError: The file exceeds `max_bytes`.
        InvalidTextFileError: The file is not valid UTF-8.
    """
    _check_upload(filename, content, allowed_exts, max_bytes)
    try:
        text = content.decode("utf-8-sig")  # also strips a BOM if present
    except UnicodeDecodeError as exc:
        raise InvalidTextFileError() from exc
    if not text.strip():
        raise EmptyFileError()
    return text