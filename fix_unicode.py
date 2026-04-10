"""Fix Unicode characters in convert_report.py for fpdf2 Latin-1 compatibility."""

with open("convert_report.py", "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "\u2014": "-",     # em-dash
    "\u2013": "-",     # en-dash
    "\u2192": "->",    # right arrow
    "\u2022": "-",     # bullet
    "\u00d7": "x",     # multiplication sign
    "\u201c": '"',     # left double quote
    "\u201d": '"',     # right double quote
    "\u2018": "'",     # left single quote
    "\u2019": "'",     # right single quote
    "\u2026": "...",   # ellipsis
    "\u00b2": "^2",    # superscript 2
    "\u2248": "~",     # approximately
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open("convert_report.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed all Unicode characters.")
