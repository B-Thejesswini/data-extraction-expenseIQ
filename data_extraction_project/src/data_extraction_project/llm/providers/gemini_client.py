import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from data_extraction_project.core.exceptions import ExtractionFailedError
from data_extraction_project.llm.prompts.gemini_extraction_prompt import EXTRACTION_PROMPT
from data_extraction_project.schemas.vlm_extraction_schema import ReceiptExtraction

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self.model = model

    async def extract_receipt(self, image_bytes: bytes, mime_type: str) -> ReceiptExtraction:
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=[
                    EXTRACTION_PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReceiptExtraction,
                    temperature=0,
                ),
            )
        except Exception as exc:
            logger.exception("Gemini request failed")
            raise ExtractionFailedError() from exc

        if not response.text:  # e.g. blocked or empty candidate
            logger.error("Gemini returned no text")
            raise ExtractionFailedError()

        try:
            return ReceiptExtraction.model_validate_json(response.text)
        except ValidationError as exc:
            logger.error("Gemini returned invalid JSON: %s", response.text)
            raise ExtractionFailedError() from exc