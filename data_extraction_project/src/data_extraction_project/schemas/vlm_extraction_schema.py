from pydantic import BaseModel


class LineItem(BaseModel):
    item_name: str
    quantity: float | None
    cost_per_item: float | None


class ReceiptExtraction(BaseModel):
    merchant: str | None
    amount: float | None
    currency: str | None
    expense_date: str | None
    category: str | None
    category_confidence: float | None
    extraction_confidence: float | None
    is_readable: bool
    line_items: list[LineItem]


class ExtractionResponse(BaseModel):
    model: str
    latency_s: float
    data: ReceiptExtraction