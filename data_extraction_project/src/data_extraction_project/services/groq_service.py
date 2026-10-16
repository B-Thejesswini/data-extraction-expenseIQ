import time

from data_extraction_project.llm.providers.groq_client import GroqClient
from data_extraction_project.core.constants import GROQ_IMAGE_MIME_TYPES
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.validate_uploaded_image import validate_image_upload


class GroqService:
    def __init__(self, client: GroqClient, max_upload_bytes: int) -> None:
        """Set up the service with its Groq client and upload size limit.

    Args:
        client: Groq client used for all extraction calls.
        max_upload_bytes: Largest image accepted, in bytes. Should not exceed what
            Groq accepts, since base64 encoding inflates the payload by about 33%.
    """
        self._client = client
        self._max_upload_bytes = max_upload_bytes

    async def extract(self, filename: str, content: bytes) -> ExtractionResponse:
        """Extract receipt data from an uploaded image.

    Validates the file type and size, sends the image to Groq, and returns the
    structured result. `latency_s` measures the Groq call only.

    Args:
        filename: Original upload name, used to determine the image type.
        content: Raw image bytes.

    Returns:
        The model name, Groq call latency in seconds, and the extracted receipt data.

    Raises:
        UnsupportedFileTypeError: Extension is not a Groq-supported image format.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_upload_bytes`.
        ExtractionFailedError: Groq failed or returned unparseable output.
    """
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