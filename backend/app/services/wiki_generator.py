import os
import re
import markdown
from bs4 import BeautifulSoup

def generate_wiki_html(md_text, base_name, output_dir):
    """
    Converts Markdown text to a styled Wikipedia-like HTML page.
    Includes TOC extraction, figure repositioning, and collapsible sections.
    """
    # We intentionally do NOT prepend the title here anymore because the Mistral summary
    # typically provides its own title, or the frontend Vue wrapper handles it.
        
    print("Converting Markdown to HTML...")
    # Convert markdown to HTML with Table of Contents and Table support
    md = markdown.Markdown(extensions=['toc', 'tables', 'fenced_code'])
    html_content = md.convert(md_text)
    toc_html = md.toc
    
    # Post-process with BeautifulSoup for figure repositioning
    soup = BeautifulSoup(html_content, "html.parser")
    import fitz
    
    # 1. First extract all images and group them if adjacent
    images = soup.find_all('img')
    grouped_images = []
    
    current_group = []
    for img in images:
        if not current_group:
            current_group.append(img)
        else:
            prev_img = current_group[-1]
            p_curr = img.find_parent('p')
            p_prev = prev_img.find_parent('p')
            
            if p_curr and p_prev and p_curr == p_prev:
                current_group.append(img)
            elif p_curr and p_prev:
                curr_node = p_prev.next_sibling
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

    # 2. Process groups and assign CSS containers
    for group in grouped_images:
        # Determine insertion point
        insertion_node = group[0].find_parent('p') or group[0]
        
        # Optional parent wrapper if multiple images
        if len(group) > 1:
            group_div = soup.new_tag(
                "div", 
                attrs={"class": "wiki-figure-group", "style": "display: flex; justify-content: center; gap: 1em; flex-wrap: wrap; margin: 1.5em auto;"}
            )
            insertion_node.insert_before(group_div)
            container = group_div
        else:
            container = None
            
        for img in group:
            p = img.find_parent('p')
            
            # Read true image width to constrain the container
            img_width = None
            src = img.get('src', '')
            if os.path.exists(src):
                try:
                    px = fitz.Pixmap(src)
                    img_width = px.width
                    px = None
                except Exception as e:
                    print(f"Could not read image width for {src}: {e}")
                    
            # Set inline style to shrink the figure container to the image width
            style = f"width: {img_width}px;" if img_width else "width: max-content;"
            
            figure_class = "wiki-figure center"
            figure_div = soup.new_tag("div", attrs={"class": figure_class, "style": style})
            
            if container:
                container.append(figure_div)
                # clear vertical margins for flex items so they align nicely inside the flex row
                figure_div['style'] += " margin: 0;"
            else:
                insertion_node.insert_before(figure_div)
            
            # Extract image from original location and put it in figure_div
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
            

            
    # Assembly with Template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }} /* Prevent double scrollbars in iframe */
        {css_content}
        .header-toggle {{ cursor: pointer; user-select: none; }}
        .header-toggle::before {{
            content: '▼'; font-size: 0.6em; display: inline-block;
            margin-right: 8px; transition: transform 0.2s; vertical-align: middle;
        }}
        .header-toggle.collapsed::before {{ transform: rotate(-90deg); }}
        .collapsed-content {{ display: none !important; }}
        
        .highlight-popup {{
            position: absolute;
            background-color: #fff;
            color: #202122;
            padding: 12px;
            border: 1px solid #a2a9b1;
            border-radius: 28px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-width: 350px;
            z-index: 1000;
            display: none;
            font-size: 0.9em;
            line-height: 1.5;
            font-family: sans-serif;
        }}
        .highlight-popup .loading {{
            color: #54595d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div id="highlight-popup" class="highlight-popup">
        <div id="highlight-popup-content"></div>
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

            // Text Highlight Popup Logic
            let descCache = {{ text: null, error: null }};

            document.addEventListener('mouseup', function(e) {{
                const popup = document.getElementById('highlight-popup');
                if (popup.contains(e.target)) return;

                const selection = window.getSelection();
                const text = selection.toString().trim();
                
                if (text.length > 0) {{ 
                    const range = selection.getRangeAt(0);
                    const rect = range.getBoundingClientRect();
                    
                    popup.style.display = 'block';
                    descCache = {{ text: null, error: null }};
                    
                    const contentDiv = document.getElementById('highlight-popup-content');
                    contentDiv.innerText = 'Explain';
                    
                    // Style the popup to look like a button
                    popup.style.cursor = 'pointer';
                    popup.style.background = '#ffffff';
                    popup.style.border = '1px solid #a2a9b1';
                    popup.style.padding = '8px 16px';
                    popup.style.fontWeight = 'bold';
                    popup.style.textAlign = 'center';
                    
                    popup.onclick = function() {{
                        popup.onclick = null; // Remove listener
                        popup.style.cursor = 'auto';
                        popup.style.background = '#fff';
                        popup.style.padding = '12px';
                        popup.style.fontWeight = 'normal';
                        popup.style.textAlign = 'left';
                        
                        if (descCache.text) {{
                            contentDiv.innerText = descCache.text;
                        }} else if (descCache.error) {{
                            contentDiv.innerHTML = '<span style="color:red">Failed to generate description.</span>';
                        }} else {{
                            contentDiv.innerHTML = '<span class="loading">Generating description...</span>';
                        }}
                    }};
                    
                    const topPos = rect.top + window.scrollY - popup.offsetHeight - 10;
                    popup.style.left = Math.max(10, rect.left + window.scrollX) + 'px';
                    popup.style.top = Math.max(10, topPos) + 'px';
                    
                    // Since the HTML is hosted on S3 and rendered in an iframe, we need to explicitly call the local backend
                    // You might need a more robust way to inject the backend URL in production.
                    const apiUrl = "http://localhost:8000/papers/description";

                    fetch(apiUrl, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text }})
                    }})
                    .then(res => {{
                        if (!res.ok) throw new Error("Network response was not ok");
                        return res.json();
                    }})
                    .then(data => {{
                        descCache.text = data.markdown || "No description generated.";
                        if (contentDiv.querySelector('.loading')) {{
                            contentDiv.innerText = descCache.text;
                            
                            setTimeout(() => {{
                                const newTop = rect.top + window.scrollY - popup.offsetHeight - 10;
                                popup.style.top = Math.max(10, newTop) + 'px';
                            }}, 0);
                        }}
                    }})
                    .catch(err => {{
                        console.error("Popup Error:", err);
                        descCache.error = true;
                        if (contentDiv.querySelector('.loading')) {{
                            contentDiv.innerHTML = '<span style="color:red">Failed to generate description.</span>';
                        }}
                    }});
                }} else {{
                    popup.style.display = 'none';
                }}
            }});

            document.addEventListener('mousedown', function(e) {{
                const popup = document.getElementById('highlight-popup');
                if (popup.style.display === 'block' && !popup.contains(e.target)) {{
                    popup.style.display = 'none';
                    popup.onclick = null;
                }}
            }});

            // Send dynamic height to parent wrapper (Vue)
            function sendHeight() {{
                const height = document.documentElement.scrollHeight;
                window.parent.postMessage({{ type: 'resize', height: height }}, '*');
            }}
            window.addEventListener('load', sendHeight);
            new ResizeObserver(sendHeight).observe(document.body);
        }});
    </script>
</body>
</html>
"""
    return html_template
