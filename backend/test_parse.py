import re
from app.services.wiki_parser import parse_pdf_to_markdown

md_text = parse_pdf_to_markdown("app/assets/papers/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION.pdf", "tmp_images")
headers = re.findall(r'^(#{1,3}\s+.*)', md_text, re.MULTILINE)
for h in headers:
    print(h)
