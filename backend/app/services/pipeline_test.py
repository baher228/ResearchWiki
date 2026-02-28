"""
Full pipeline test: PDF -> Parse (text + images) -> Mistral summarization -> Wiki HTML output

Usage:
    python -m app.services.pipeline_test [path_to_pdf]

If no path is given, uses the DIAYN paper from assets/papers/.
"""

import sys
import os
import asyncio
import webbrowser

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.mistral_service import summarize_paper
from app.services.wiki_generator import generate_wiki_html


async def run_pipeline(pdf_path: str):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    pages_dir = os.path.join(assets_dir, "pages")
    images_dir = os.path.join(pages_dir, f"{base_name}_images")
    md_dir = os.path.join(assets_dir, "markdowns")

    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    # ── Phase 1: Parse PDF ──────────────────────────────────────────────
    print("=" * 60)
    print("PHASE 1: Parsing PDF")
    print("=" * 60)
    print(f"  PDF: {pdf_path}")
    print(f"  Images dir: {images_dir}")

    raw_md = parse_pdf_to_markdown(pdf_path, images_dir)
    print(f"  ✓ Extracted {len(raw_md):,} chars of text")

    # Count extracted images
    image_files = [f for f in os.listdir(images_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
    print(f"  ✓ Extracted {len(image_files)} images")

    # Save the raw parsed markdown for reference
    raw_md_path = os.path.join(md_dir, f"{base_name}_RAW.md")
    with open(raw_md_path, "w", encoding="utf-8") as f:
        f.write(raw_md)
    print(f"  ✓ Raw markdown saved: {raw_md_path}")

    # ── Phase 2: Mistral Summarization ──────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 2: Mistral Summarization (with image awareness)")
    print("=" * 60)

    summary_md = await summarize_paper(raw_md)
    print(f"  ✓ Summary: {len(summary_md):,} chars (condensed from {len(raw_md):,})")
    print(f"  ✓ Compression ratio: {len(raw_md) / max(len(summary_md), 1):.1f}x")

    # Check how many images made it into the summary
    import re
    img_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', summary_md)
    print(f"  ✓ Images referenced in summary: {len(img_refs)}")
    for alt, path in img_refs:
        print(f"    - {alt or '(no caption)'} → {os.path.basename(path)}")

    # Save summarized markdown
    summary_md_path = os.path.join(md_dir, f"{base_name}_SUMMARY.md")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    print(f"  ✓ Summary markdown saved: {summary_md_path}")

    # ── Phase 3: Generate Wiki HTML ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 3: Generating Wiki HTML")
    print("=" * 60)

    html_output = generate_wiki_html(summary_md, base_name, pages_dir)

    output_html_path = os.path.join(pages_dir, f"{base_name}_SUMMARY.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"  ✓ Wiki HTML saved: {output_html_path}")

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Input PDF:        {pdf_path}")
    print(f"  Raw markdown:     {raw_md_path}")
    print(f"  Summary markdown: {summary_md_path}")
    print(f"  Wiki HTML:        {output_html_path}")
    print(f"  Images used:      {len(img_refs)} of {len(image_files)} extracted")

    # Open in browser
    webbrowser.open(f"file://{output_html_path}")
    print(f"\n  Opened in browser!")


async def main():
    if len(sys.argv) >= 2:
        pdf_path = sys.argv[1]
    else:
        # Default to the DIAYN paper
        pdf_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "assets", "papers",
            "DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION.pdf"
        ))

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        sys.exit(1)

    await run_pipeline(pdf_path)


if __name__ == "__main__":
    asyncio.run(main())
