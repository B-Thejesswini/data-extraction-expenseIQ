from pydantic import BaseModel


class OCRResponse(BaseModel):
    rec_texts: list[str]
    rec_scores: list[float]


class TesseractResponse(BaseModel):
    text: list[str]
    conf: list[int]  # 0-100 scale, unlike PaddleOCR's 0-1