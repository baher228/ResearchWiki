from pydantic import BaseModel, Field
from typing import Optional


class SummarizeRequest(BaseModel):
    """Request body for paper summarization (raw text input)."""

    text: str = Field(
        ...,
        min_length=50,
        description="The full text content of the research paper to summarize.",
    )


class SummarizeResponse(BaseModel):
    """Wiki-style markdown summary returned to the client."""

    title: str = Field(..., description="The paper title extracted from the markdown.")
    markdown: str = Field(..., description="Full wiki-style markdown content.")


class PipelineResponse(BaseModel):
    """Full pipeline response: summarized markdown + generated wiki HTML."""

    title: str = Field(..., description="The paper title extracted from the markdown.")
    markdown: str = Field(..., description="Summarized wiki-style markdown content.")
    html_url: str = Field(..., description="URL path to the generated wiki HTML page.")
    markdown_url: str = Field(..., description="URL path to the saved summary markdown.")
    images_used: int = Field(0, description="Number of figures referenced in the summary.")
    images_extracted: int = Field(0, description="Total number of images extracted from the PDF.")
