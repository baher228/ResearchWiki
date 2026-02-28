#TEST SCRIPT — Feed a full paper through mistral_service.summarize_paper

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.mistral_service import summarize_paper

async def main():
    # Use the DIAYN paper as test input
    pdf_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "assets", "papers",
        "DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION.pdf"
    ))

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    print(f"Parsing PDF: {pdf_path}")
    images_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "assets", "pages", "test_images"
    ))
    os.makedirs(images_dir, exist_ok=True)
    paper_text = parse_pdf_to_markdown(pdf_path, images_dir)
    print(f"Parsed {len(paper_text)} chars of text from PDF.\n")

    print("Sending to Mistral for summarization...")
    result = await summarize_paper(paper_text)

    print("\n" + "=" * 60)
    print("SUMMARIZED MARKDOWN OUTPUT")
    print("=" * 60 + "\n")
    print(result)

    # Save output for comparison
    out_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "assets", "markdowns",
        "DIAYN_SUMMARY_TEST.md"
    ))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved to: {out_path}")

if __name__ == "__main__":
    asyncio.run(main())