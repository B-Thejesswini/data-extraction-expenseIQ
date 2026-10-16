import io
import json
import re
from datetime import datetime
from pathlib import Path

import pytesseract
from PIL import Image, ImageDraw
from pytesseract import Output

from data_extraction_project.core.exceptions import UnsupportedFileTypeError
from data_extraction_project.schemas.ocr_schema import TesseractResponse

from data_extraction_project.core.constants import IMAGE_EXTS
from data_extraction_project.core.config import settings


class TesseractService:
    def __init__(self, results_dir: Path = settings.tesseract_results_dir, psm: int = settings.tesseract_psm) -> None:
        """Create the output folder and configure Tesseract.

        Requires the Tesseract binary to be installed on the machine, since
        `pytesseract` is only a wrapper around it.

        Args:
            results_dir: Folder where annotated images, preprocessed images and raw JSON
                are saved. Created if it does not exist.
            psm: Tesseract page segmentation mode. 6 treats the image as a single uniform
                block of text, which suits most receipts. Try 4 (single column, variable
                font sizes) if a layout confuses it.
        """
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        # PSM 6: single uniform block of text. Try 4 for single-column,
        # variable font size layouts.
        self._config = f"--psm {psm}"

    def extract(self, filename: str, content: bytes) -> TesseractResponse:
        """Run Tesseract OCR on an uploaded image and save the artifacts.

        Blocking, so call it from a worker thread rather than directly on the event
        loop. Unlike PaddleOCR there is no shared model state, so concurrent calls are
        safe. Each call saves three files to `results_dir`, sharing a timestamp:
        `<name>_res_img_<ts>.jpg` (word boxes drawn on the image, red when confidence is
        below `tesseract_low_conf_threshold` and green otherwise),
        `<name>_preprocessed_img_<ts>.jpg` (the RGB-converted input, since no other
        preprocessing is applied), and `<name>_<ts>_.json` (text, confidences, and the
        raw Tesseract output including box coordinates).

        Args:
            filename: Original upload name, used for the file type and output names.
                Characters other than letters, digits, `_` and `-` are replaced with `_`.
            content: Raw image bytes.

        Returns:
            The recognized words and their confidence scores, in matching order.
            Confidence is on a 0 to 100 scale, unlike PaddleOCR's 0 to 1. Empty words
            and regions Tesseract marks as non-text are skipped.

        Raises:
            UnsupportedFileTypeError: Extension is not in `IMAGE_EXTS`.
            PIL.UnidentifiedImageError: The content is not a readable image. This is not
                yet mapped to `InvalidImageError`, so it currently surfaces as a 500.
        """
        suffix = Path(filename).suffix.lower()
        if suffix not in IMAGE_EXTS:
            raise UnsupportedFileTypeError(
                suffix=suffix,
                allowed=sorted(IMAGE_EXTS),
            )

        stem = re.sub(r"[^A-Za-z0-9_-]", "_", Path(filename).stem) or "upload"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        image = Image.open(io.BytesIO(content)).convert("RGB")
        data = pytesseract.image_to_data(
            image, output_type=Output.DICT, config=self._config
        )

        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)

        texts: list[str] = []
        confs: list[int] = []
        for i in range(len(data["text"])):
            word = data["text"][i].strip()
            conf = int(float(data["conf"][i]))  # newer pytesseract may return "96.5"
            if not word or conf < 0:  # -1 means "not a text region"
                continue

            texts.append(word)
            confs.append(conf)

            x, y = data["left"][i], data["top"][i]
            w, h = data["width"][i], data["height"][i]
            color = "red" if conf < settings.tesseract_low_conf_threshold else "lime"
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)

        # Persist artifacts with the required naming convention.
        annotated.save(self._results_dir / f"{stem}_res_img_{timestamp}.jpg", "JPEG")
        image.save(self._results_dir / f"{stem}_preprocessed_img_{timestamp}.jpg", "JPEG")
        (self._results_dir / f"{stem}_{timestamp}_.json").write_text(
            json.dumps({"text": texts, "conf": confs, "raw": data}, indent=2)
        )

        return TesseractResponse(text=texts, conf=confs)