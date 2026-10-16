import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from data_extraction_project.core.exceptions import ExtractionFailedError
from data_extraction_project.llm.prompts.gemini_extraction_prompt import EXTRACTION_PROMPT, MARKDOWN_EXTRACTION_PROMPT
from data_extraction_project.schemas.vlm_extraction_schema import ReceiptExtraction

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        """Create the Gemini API client.

        A single instance is meant to be shared across services, since it holds one
        connection pool for both the sync and async APIs.

        Args:
            api_key: Gemini API key.
            model: Model name used for every request, for example `gemini-2.5-flash`.
                Also exposed as the public `model` attribute.
        """
        self._client = genai.Client(api_key=api_key)
        self.model = model

    async def extract_receipt(self, image_bytes: bytes, mime_type: str) -> ReceiptExtraction:
        """Extract receipt data from an image using the image prompt.

        Args:
            image_bytes: Raw image bytes.
            mime_type: MIME type of the image, such as `image/jpeg`. It must be a format
                Gemini accepts.

        Returns:
            The parsed and validated receipt data.

        Raises:
            ExtractionFailedError: The request failed, Gemini returned no text, or the
                output did not match `ReceiptExtraction`.
        """
        return await self._generate(
            [EXTRACTION_PROMPT, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
        )

    async def extract_receipt_from_text(self, text: str) -> ReceiptExtraction:
        """Extract receipt data from text, such as markdown converted from a PDF.

        The text is wrapped in `<document>` tags, and the prompt tells the model to treat
        it as data, not instructions. This reduces the risk of prompt injection from
        untrusted documents but does not remove it.

        Args:
            text: Full text of the receipt or invoice. Size limits are the caller's
                responsibility.

        Returns:
            The parsed and validated receipt data.

        Raises:
            ExtractionFailedError: The request failed, Gemini returned no text, or the
                output did not match `ReceiptExtraction`.
        """
        return await self._generate(
            [MARKDOWN_EXTRACTION_PROMPT, f"<document>\n{text}\n</document>"]
        )

    async def _generate(self, contents: list[str | types.Part]) -> ReceiptExtraction:
        """Send a request to Gemini and parse the structured response.

        Shared by the image and text paths. Requests JSON output constrained to the
        `ReceiptExtraction` schema, with temperature 0 for repeatable results. Details
        of any failure are logged and never exposed to the caller.

        Args:
            contents: Prompt text followed by the input, as plain strings or image parts.

        Returns:
            The parsed and validated receipt data.

        Raises:
            ExtractionFailedError: The API call raised, the response had no text (for
                example a blocked or empty candidate), or the text was not valid JSON for
                `ReceiptExtraction`.
        """
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=contents,
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