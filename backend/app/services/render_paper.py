import sys
import os
import webbrowser

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.wiki_generator import generate_wiki_html

def main():
    if len(sys.argv) < 2:
        print("Usage: python render_paper.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: Could not find file {pdf_path}")
        sys.exit(1)
        
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "pages"))
    
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)
        
    images_dir = os.path.join(pages_dir, f"{base_name}_images")
    
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        
    from app.services.mistral_service import summarize_paper
    import asyncio

    # Phase 1: Parsing
    md_text = parse_pdf_to_markdown(pdf_path, images_dir)
    
    orig_md_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "original_markdowns"))
    if not os.path.exists(orig_md_dir):
        os.makedirs(orig_md_dir)
        
    output_md_path = os.path.join(orig_md_dir, f"{base_name}.md")
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
        
    print(f"Extracted {len(md_text)} chars of text.")
    print("Running Mistral summarization...")
    
    # Phase 2: AI Summarization
    summary_md = asyncio.run(summarize_paper(md_text))
    
    mistral_md_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "mistral_markdowns"))
    if not os.path.exists(mistral_md_dir):
        os.makedirs(mistral_md_dir)
        
    summary_md_path = os.path.join(mistral_md_dir, f"{base_name}_SUMMARY.md")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    
    # Phase 3: Generating HTML
    html_output = generate_wiki_html(summary_md, base_name, pages_dir)
    
    # Save Output
    output_html_path = os.path.join(pages_dir, f"{base_name}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"Successfully generated Wikipedia-style page: {output_html_path}")
    
    # Open in default browser
    webbrowser.open(f"file://{output_html_path}")

if __name__ == "__main__":
    main()
