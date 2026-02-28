import os
import re
import markdown
from bs4 import BeautifulSoup

def generate_wiki_html(md_text, base_name, output_dir):
    """
    Converts Markdown text to a styled Wikipedia-like HTML page.
    Includes TOC extraction, figure repositioning, and collapsible sections.
    """
    # Add a main title for the document if not present
    if not md_text.lstrip().startswith("# "):
        md_text = f"# {base_name.replace('_', ' ')}\n\n" + md_text
        
    print("Converting Markdown to HTML...")
    # Convert markdown to HTML with Table of Contents and Table support
    md = markdown.Markdown(extensions=['toc', 'tables', 'fenced_code'])
    html_content = md.convert(md_text)
    toc_html = md.toc
    
    # Post-process with BeautifulSoup for figure repositioning
    soup = BeautifulSoup(html_content, "html.parser")
    
    for p in soup.find_all('p'):
        text = p.get_text(separator=" ").strip()
        match = re.match(r'^(?:Figure|Fig\.?)\s+(\d+)', text, re.IGNORECASE)
        if match:
            fig_num = match.group(1)
            
            images_to_bundle = []
            curr = p.previous_sibling
            nodes_to_remove = []
            
            # Look back up to 15 elements to find images for this figure
            for _ in range(15):
                if not curr: break
                if curr.name == 'p' and curr.find('img'):
                    images_to_bundle.extend(curr.find_all('img'))
                    nodes_to_remove.append(curr)
                elif curr.name == 'img':
                    images_to_bundle.append(curr)
                    nodes_to_remove.append(curr)
                elif curr.name in ['h1', 'h2', 'h3', 'h4']: 
                    break
                curr = curr.previous_sibling
                
            if not images_to_bundle:
                continue
                
            figure_div = soup.new_tag("div", attrs={"class": "wiki-figure"})
            for img in reversed(images_to_bundle):
                figure_div.append(img.extract())
                
            for node in nodes_to_remove:
                if not node.get_text(strip=True) and not node.find('img'):
                    node.decompose()
                    
            caption_div = soup.new_tag("div", attrs={"class": "wiki-caption"})
            for child in list(p.contents):
                caption_div.append(child.extract())
            figure_div.append(caption_div)
            
            ref_pattern = re.compile(rf'(?:Figure|Fig\.?)\s+{fig_num}\b', re.IGNORECASE)
            placed = False
            for tag in soup.find_all('p'):
                if tag == p or figure_div in tag.parents:
                    continue
                if ref_pattern.search(tag.get_text()):
                    tag.insert_before(figure_div)
                    placed = True
                    break
                    
            if not placed:
                p.insert_before(figure_div)
                
            p.decompose()
            
    html_content = str(soup)
    
    # Load CSS and Logo
    import base64
    pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "pages"))
    css_path = os.path.join(pages_dir, "wikipedia_style.css")
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            
    logo_path = os.path.join(pages_dir, "WikiResearch.png")
    logo_src = "WikiResearch.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
            logo_src = f"data:image/png;base64,{b64_img}"
            
    # Assembly with Template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
    <style>
        {css_content}
        .header-toggle {{ cursor: pointer; user-select: none; }}
        .header-toggle::before {{
            content: '▼'; font-size: 0.6em; display: inline-block;
            margin-right: 8px; transition: transform 0.2s; vertical-align: middle;
        }}
        .header-toggle.collapsed::before {{ transform: rotate(-90deg); }}
        .collapsed-content {{ display: none !important; }}
    </style>
</head>
<body>
    <div class="wiki-header">
        <div class="header-logo">
            <img src="{logo_src}" alt="Wikipedia Logo">
            <span class="header-logo-text">WikiResearch</span>
        </div>
        <div class="header-search">
            <input type="text" placeholder="Search WikiResearch">
        </div>
    </div>
    <div class="wiki-container">
        <div class="wiki-sidebar">
            <div class="sidebar-header">Contents</div>
            {toc_html}
        </div>
        <div class="wiki-content">
            {html_content}
        </div>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const headings = document.querySelectorAll('.wiki-content h1, .wiki-content h2, .wiki-content h3, .wiki-content h4, .wiki-content h5, .wiki-content h6');
            headings.forEach(heading => {{
                if (heading.tagName === 'H1' && heading === headings[0]) return;
                heading.classList.add('header-toggle');
                heading.addEventListener('click', function() {{
                    this.classList.toggle('collapsed');
                    const level = parseInt(this.tagName.substring(1));
                    let curr = this.nextElementSibling;
                    while (curr) {{
                        const isHeading = curr.tagName.match(/^H[1-6]$/);
                        if (isHeading) {{
                            const currLevel = parseInt(curr.tagName.substring(1));
                            if (currLevel <= level) break;
                        }}
                        curr.classList.toggle('collapsed-content');
                        curr = curr.nextElementSibling;
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>
"""
    return html_template
