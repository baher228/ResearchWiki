import sys
import os
import webbrowser
from wiki_parser import parse_pdf_to_markdown
from wiki_generator import generate_wiki_html

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
        
    # Phase 1: Parsing
    md_text = parse_pdf_to_markdown(pdf_path, images_dir)
    
    md_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "markdowns"))
    if not os.path.exists(md_dir):
        os.makedirs(md_dir)
        
    output_md_path = os.path.join(md_dir, f"{base_name}.md")
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    
    # Phase 2: Generating
    html_output = generate_wiki_html(md_text, base_name, pages_dir)
    
    # Save Output
    output_html_path = os.path.join(pages_dir, f"{base_name}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"Successfully generated Wikipedia-style page: {output_html_path}")
    
    # Open in default browser
    webbrowser.open(f"file://{output_html_path}")

if __name__ == "__main__":
    main()
