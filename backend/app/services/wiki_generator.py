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
    import fitz
    
    # 1. First extract all images and wrap them
    images = soup.find_all('img')
    grouped_images = []
    
    # Group images that belong together (in the same p tag or consecutive p tags)
    current_group = []
    for img in images:
        if not current_group:
            current_group.append(img)
        else:
            prev_img = current_group[-1]
            # They are grouped if they share a parent or their parents are siblings contiguous
            p_curr = img.find_parent('p')
            p_prev = prev_img.find_parent('p')
            
            if p_curr and p_prev and p_curr == p_prev:
                current_group.append(img)
            elif p_curr and p_prev:
                # Check if p_prev is immediately before p_curr
                curr_node = p_prev.next_sibling
                is_consecutive = False
                while curr_node and curr_node != p_curr:
                    if curr_node.name and curr_node.name != 'br':
                        break
                    curr_node = curr_node.next_sibling
                
                if curr_node == p_curr:
                    current_group.append(img)
                else:
                    grouped_images.append(current_group)
                    current_group = [img]
            else:
                grouped_images.append(current_group)
                current_group = [img]
                    
    if current_group:
        grouped_images.append(current_group)

    # 2. Process groups and assign CSS classes based on width/count
    for group in grouped_images:
        is_wide = False
        if len(group) > 1:
            is_wide = True
        else:
            img = group[0]
            src = img.get('src', '')
            if os.path.exists(src):
                try:
                    px = fitz.Pixmap(src)
                    if px.width > 500:
                        is_wide = True
                    # Clean up the pixmap to free memory
                    px = None
                except Exception as e:
                    print(f"Could not read image width for {src}: {e}")
                    
        figure_class = "wiki-figure center" if is_wide else "wiki-figure right"
        figure_div = soup.new_tag("div", attrs={"class": figure_class})
        
        # Determine insertion point (before the parent <p> of the first image, or the image itself)
        insertion_node = group[0].find_parent('p') or group[0]
        
        # Insert the figure container into the DOM first
        insertion_node.insert_before(figure_div)
        
        for img in group:
            p = img.find_parent('p')
            figure_div.append(img.extract())
            
            # Extract caption from alt text
            alt_text = img.get('alt', '').strip()
            if alt_text:
                caption_div = soup.new_tag("div", attrs={"class": "wiki-caption"})
                caption_div.string = alt_text
                figure_div.append(caption_div)
            
            # If the p is now empty, kill it
            if p and not p.get_text(strip=True) and not p.find('img'):
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
