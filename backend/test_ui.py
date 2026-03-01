import sys
import os
import webbrowser

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from services.wiki_generator import generate_wiki_html

def main():
    base_name = "Test_Paper"
    pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "assets", "pages"))
    
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)
        
    print("Generating dummy markdown levels...")

    # Create dummy markdown with different complexity levels for the UI testing
    level_1 = """# Introduction to Something Complex
This is the longest, most academic summarization. It is meant to represent Complexity Level 1.
It includes deep details, complex terminology, and extensive context.

## Methodology
We used a highly nuanced approach...
Here is a list of things:
- Item 1
- Item 2

### Sub-details
Even more text here to show the slider works!
"""

    level_3 = """# Intro to Something
This is a medium-length summary. It is meant to represent Complexity Level 3.
It balances detail with readability.

## Method
We did some things...
- Item A
- Item B
"""

    level_5 = """# The Basics
This is the absolute simplest summary. It represents Complexity Level 5.
It is very short and uses plain English.

1. We tried something.
2. It worked.
"""

    summaries = [level_1, level_3, level_5]
    
    # Generate HTML
    print("Running generate_wiki_html...")
    html_output = generate_wiki_html(summaries, base_name, pages_dir)
    
    # Save Output
    output_html_path = os.path.join(pages_dir, f"{base_name}_test.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"Successfully generated Wikipedia-style test page: {output_html_path}")
    
    # Open in default browser
    webbrowser.open(f"file://{output_html_path}")

if __name__ == "__main__":
    main()
