import time
from pathlib import Path

from data_extraction_project.llm.providers.gemini_client import GeminiClient
from data_extraction_project.core.constants import GEMINI_IMAGE_MIME_TYPES
from data_extraction_project.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse


class GeminiService:
    def __init__(self, client: GeminiClient, max_upload_bytes: int) -> None:
        self._client = client
        self._max_upload_bytes = max_upload_bytes

    async def extract(self, filename: str, content: bytes) -> ExtractionResponse:
        mime_type = self._validate(filename, content)

        start = time.perf_counter()
        data = await self._client.extract_receipt(content, mime_type)
        latency = time.perf_counter() - start

        return ExtractionResponse(
            model=self._client.model,
            latency_s=round(latency, 3),
            data=data,
        )

    def _validate(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        mime_type = GEMINI_IMAGE_MIME_TYPES.get(suffix)
        if mime_type is None:
            raise UnsupportedFileTypeError(
                suffix=suffix or "(none)",
                allowed=", ".join(sorted(GEMINI_IMAGE_MIME_TYPES)),
            )
        if not content:
            raise EmptyFileError()
        if len(content) > self._max_upload_bytes:
            raise FileTooLargeError(max_mb=self._max_upload_bytes // (1024 * 1024))
        return mime_type