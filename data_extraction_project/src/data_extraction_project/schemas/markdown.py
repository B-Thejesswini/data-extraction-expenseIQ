from pydantic import BaseModel


class MarkdownResponse(BaseModel):
    markdown: str