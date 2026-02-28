import os
import re
import pymupdf4llm

def parse_pdf_to_markdown(pdf_path, images_dir):
    """
    Extracts text as Markdown and images from a PDF using pymupdf4llm.
    Includes post-processing to fix heading levels based on numbering.
    """
    print(f"Extracting text and images from {pdf_path}...")
    
    # pymupdf4llm extracts markdown and saves images
    md_text = pymupdf4llm.to_markdown(
        doc=pdf_path,
        write_images=True,
        image_path=images_dir,
        image_format="png",
        dpi=150
    )
    
    # Post-process the extracted markdown to identify headers that pymupdf4llm missed
    lines = md_text.split('\n')
    for i, line in enumerate(lines):
        s = line.strip()
        # Filter for relatively short lines that might be headers
        if 0 < len(s) < 100:
            # 1. Exact match for common unnumbered top-level headers (all caps)
            if re.match(r'^(ABSTRACT|INTRODUCTION|REFERENCES|ACKNOWLEDGMENTS|CONCLUSION|APPENDIX\s+[A-Z])$', s, re.IGNORECASE) and s.isupper():
                lines[i] = f"## {s}"
            # 2. Match numbered headers like "1 INTRODUCTION", "3.1 HOW IT WORKS", "IV. METHOD"
            elif re.match(r'^([0-9IVX]+\.?)+\s+[A-Z][A-Z0-9\s:\-]+$', s):
                # Count dots to determine nesting depth (0 dots = level 2, 1 dot = level 3, etc.)
                num_dots = s.split(' ', 1)[0].count('.')
                # Cap the heading level at 6
                level = min(6, 2 + num_dots)
                hashes = "#" * level
                lines[i] = f"{hashes} {s}"
    
    return '\n'.join(lines)
