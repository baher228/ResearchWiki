import re

text = """
## Section 1
Blah blah
![fig1](path1)

## Section 2
Blah blah 2
![fig2](path2)
"""

chunks = re.split(r'\n(?=##\s)', text)
chunks = [c.strip() for c in chunks if c.strip()]

for chunk in chunks:
    images = []
    lines = chunk.split("\n")
    for i, line in enumerate(lines):
        match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if match:
            images.append(match.group(2))
    print(f"Section starts with: {chunk[:20]}")
    print(f"Images in section: {images}")
