from pydantic import BaseModel, Field
from typing import Optional


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50)


class SummarizeResponse(BaseModel):
    title: str
    markdown: str


class PipelineResponse(BaseModel):
    id: str = Field(..., description="Paper UUID from the database.")
    title: str
    markdown: str
    html_url: str
    markdown_url: str
    images_used: int = 0
    images_extracted: int = 0
    created_at: str = ""
