import json
import re
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from paddleocr import PaddleOCR
from PIL import Image

from data_extraction_project.core.exceptions import UnsupportedFileTypeError
from data_extraction_project.schemas.ocr_schema import OCRResponse

from data_extraction_project.core.constants import IMAGE_EXTS

from data_extraction_project.core.config import settings 

class PaddleOCRService:
    def __init__(self, results_dir: Path = settings.paddleocr_results_dir) -> None:
        """Create the output folder and load the PaddleOCR models.

    Models are loaded once here because loading is the expensive part, so create a
    single instance and reuse it. Document orientation classification, unwarping and
    text-line orientation are enabled to handle tilted or curled phone photos.

    Args:
        results_dir: Folder where annotated images, preprocessed images and raw JSON
            are saved. Created if it does not exist.
    """
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)

        # Load models once; this is the expensive part.
        self._ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
        )
        # Serialize inference so concurrent requests don't share model state.
        self._lock = threading.Lock()

    def extract(self, filename: str, content: bytes) -> OCRResponse:
        """Run OCR on an uploaded image and save the artifacts.

    Blocking and CPU-bound, so call it from a worker thread rather than directly on
    the event loop. Inference is serialized with a lock, so concurrent calls run one
    at a time. Each call saves three files to `results_dir`, sharing a timestamp:
    `<name>_res_img_<ts>.jpg` (detected boxes drawn on the image),
    `<name>_preprocessed_img_<ts>.jpg` (the image after orientation/unwarping), and
    `<name>_<ts>_.json` (the full PaddleOCR result).

    Args:
        filename: Original upload name, used for the file type and output names.
            Characters other than letters, digits, `_` and `-` are replaced with `_`.
        content: Raw image bytes.

    Returns:
        The recognized text lines and their confidence scores (0 to 1), in matching order.

    Raises:
        UnsupportedFileTypeError: Extension is not in `IMAGE_EXTS`.
    """

        suffix = Path(filename).suffix.lower()
        if suffix not in IMAGE_EXTS:
            raise UnsupportedFileTypeError(
                suffix=suffix,
                allowed=sorted(IMAGE_EXTS),
            )

        stem = re.sub(r"[^A-Za-z0-9_-]", "_", Path(filename).stem) or "upload"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src = tmp_dir / f"{stem}{suffix}"
            src.write_bytes(content)

            out = tmp_dir / "out"
            out.mkdir()

            with self._lock:
                results = self._ocr.predict(str(src))

            res = results[0]
            res.save_to_img(str(out))
            res.save_to_json(str(out))

            # Persist artifacts with the required naming convention.
            self._save_image(
                out, "ocr_res_img",
                self._results_dir / f"{stem}_res_img_{timestamp}.jpg",
            )
            self._save_image(
                out, "preprocessed_img",
                self._results_dir / f"{stem}_preprocessed_img_{timestamp}.jpg",
            )

            json_src = next(out.glob("*.json"))
            shutil.copy(json_src, self._results_dir / f"{stem}_{timestamp}_.json")

            # Read back from the saved JSON (robust across PaddleOCR versions).
            data = json.loads(json_src.read_text())
            payload = data.get("res", data)

        return OCRResponse(
            rec_texts=payload.get("rec_texts", []),
            rec_scores=payload.get("rec_scores", []),
        )

    @staticmethod
    def _save_image(src_dir: Path, key: str, dest: Path) -> None:
        """Convert one PaddleOCR output image to JPEG and save it at `dest`.

    Finds the first file in `src_dir` whose name contains `key`. If none exists,
    nothing is saved and no error is raised.

    Args:
        src_dir: Folder containing PaddleOCR's raw output files.
        key: Substring identifying the image, such as `ocr_res_img` or `preprocessed_img`.
        dest: Destination path for the JPEG.
    """
        src = next(src_dir.glob(f"*{key}*"), None)
        if src is None:
            return
        Image.open(src).convert("RGB").save(dest, "JPEG")