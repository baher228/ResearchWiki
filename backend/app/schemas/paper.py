from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Request body for paper summarization."""

    text: str = Field(
        ...,
        min_length=50,
        description="The full text content of the research paper to summarize.",
    )


class SummarizeResponse(BaseModel):
    """Wiki-style markdown summary returned to the client."""

    title: str = Field(..., description="The paper title extracted from the markdown.")
    markdown: str = Field(..., description="Full wiki-style markdown content.")
