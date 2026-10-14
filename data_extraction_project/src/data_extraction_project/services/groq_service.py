import time

from data_extraction_project.llm.providers.groq_client import GroqClient
from data_extraction_project.core.constants import GROQ_IMAGE_MIME_TYPES
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.validate_uploaded_image import validate_image_upload


class GroqService:
    def __init__(self, client: GroqClient, max_upload_bytes: int) -> None:
        self._client = client
        self._max_upload_bytes = max_upload_bytes

    async def extract(self, filename: str, content: bytes) -> ExtractionResponse:
        mime_type = validate_image_upload(
            filename, content, GROQ_IMAGE_MIME_TYPES, self._max_upload_bytes
        )

        start = time.perf_counter()
        data = await self._client.extract_receipt(content, mime_type)
        latency = time.perf_counter() - start

        return ExtractionResponse(
            model=self._client.model,
            latency_s=round(latency, 3),
            data=data,
        )