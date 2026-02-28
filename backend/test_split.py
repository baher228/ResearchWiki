import re
from app.services.wiki_parser import parse_pdf_to_markdown

md_text = parse_pdf_to_markdown("app/assets/papers/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION.pdf", "tmp_images")

# split by ## 
sections = re.split(r'\n(?=## )', md_text)
print(f"Number of sections: {len(sections)}")
for s in sections:
    print(f"Section length: {len(s)}")
    print(f"Starts with: {s[:50].strip()}")
    print("---")
    
