from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Request body for paper summarization."""

    text: str = Field(
        ...,
        min_length=50,
        description="The full text content of the research paper to summarize.",
    )


class WikiSection(BaseModel):
    """A single section of the generated wiki page."""

    title: str = Field(..., description="Section heading (e.g. 'Background', 'Methodology').")
    content: str = Field(..., description="Markdown-formatted section body.")


class SummarizeResponse(BaseModel):
    """Structured wiki-style summary returned to the client."""

    title: str = Field(..., description="A concise wiki-style title for the paper.")
    summary: str = Field(..., description="A brief abstract / lead paragraph for the wiki page.")
    sections: list[WikiSection] = Field(
        default_factory=list,
        description="Ordered list of wiki sections that break down the paper.",
    )
