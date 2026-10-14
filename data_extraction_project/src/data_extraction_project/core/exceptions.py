import json
import logging
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

_CORE_DIR = Path(__file__).parent


def _load_json(filename: str) -> dict[str, Any]:
    return json.loads((_CORE_DIR / filename).read_text(encoding="utf-8"))


# code -> {"status": int, "message": str}
ERROR_CATALOG: dict[str, dict[str, Any]] = _load_json("error_catalog.json")

# HTTP status (as str) -> code. Fallback for errors the app did not raise itself.
HTTP_STATUS_CODES: dict[str, str] = _load_json("http_status_codes.json")


class AppError(Exception):
    """Base class for all application errors.

    Subclasses declare only a `code`. Status and message come from the catalog.
    Raise subclasses, never AppError itself.
    """

    code: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        code = getattr(cls, "code", None)
        if code is None:
            raise TypeError(f"{cls.__name__} must define a `code`")
        if code not in ERROR_CATALOG:
            raise ValueError(
                f"{cls.__name__}: code '{code}' is not in error_catalog.json"
            )

    def __init__(self, **context: Any) -> None:
        entry = ERROR_CATALOG[self.code]
        self.status_code: int = entry["status"]
        template: str = entry["message"]

        try:
            self.message = template.format(**context)
        except (KeyError, IndexError):
            # A raise site is missing a value the template needs. Keep the correct
            # status and code, and surface the bug in the logs instead of a 500.
            logger.warning(
                "Error '%s' raised with context %s that does not satisfy its template",
                self.code,
                sorted(context),
            )
            self.message = template

        super().__init__(self.message)


class UnsupportedFileTypeError(AppError):
    code = "UNSUPPORTED_FILE_TYPE"


class FileTooLargeError(AppError):
    code = "FILE_TOO_LARGE"


class EmptyFileError(AppError):
    code = "EMPTY_FILE"


class InvalidImageError(AppError):
    code = "INVALID_IMAGE"


class ExtractionFailedError(AppError):
    code = "EXTRACTION_FAILED"


class InvalidRequestError(AppError):
    code = "INVALID_REQUEST"


class InternalError(AppError):
    code = "INTERNAL_ERROR"