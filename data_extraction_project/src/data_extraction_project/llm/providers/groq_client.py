import base64
import json
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from data_extraction_project.core.exceptions import ExtractionFailedError
from data_extraction_project.llm.prompts.gemini_extraction_prompt import EXTRACTION_PROMPT
from data_extraction_project.schemas.vlm_extraction_schema import ReceiptExtraction
from data_extraction_project.core.config import settings

logger = logging.getLogger(__name__)


# JSON mode guarantees valid JSON but not our field names, so spell the schema out.
_PROMPT = (
    f"{EXTRACTION_PROMPT}\n\n"
    "Respond with a single JSON object that conforms to this JSON Schema:\n"
    f"{json.dumps(ReceiptExtraction.model_json_schema())}"
)


class GroqClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(base_url=settings.groq_base_url, api_key=api_key)
        self.model = model

    async def extract_receipt(self, image_bytes: bytes, mime_type: str) -> ReceiptExtraction:
        data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"

        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _PROMPT},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
            )
        except Exception as exc:
            logger.exception("Groq request failed")
            raise ExtractionFailedError() from exc

        raw_text = completion.choices[0].message.content if completion.choices else None
        if not raw_text:
            logger.error("Groq returned no content")
            raise ExtractionFailedError()

        try:
            return ReceiptExtraction.model_validate_json(raw_text)
        except ValidationError as exc:
            logger.error("Groq returned invalid JSON: %s", raw_text)
            raise ExtractionFailedError() from exc