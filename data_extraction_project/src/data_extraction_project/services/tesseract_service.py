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
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        # PSM 6: single uniform block of text. Try 4 for single-column,
        # variable font size layouts.
        self._config = f"--psm {psm}"

    def extract(self, filename: str, content: bytes) -> TesseractResponse:
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