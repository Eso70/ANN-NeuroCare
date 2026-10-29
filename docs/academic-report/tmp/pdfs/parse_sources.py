"""Prepare the three existing reports for a single typeset PDF; sources stay untouched."""
import hashlib
import json
import re
from pathlib import Path

from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
FOLDER = HERE.parents[1]
NAMES = ("project-report.md", "architecture.md", "technology-and-algorithm-reference.md")
parser = MarkdownIt("commonmark", {"html": True}).enable("table")


def encode(token):
    return {"type": token.type, "tag": token.tag, "level": token.level,
            "content": token.content, "markup": token.markup, "attrs": token.attrs,
            "children": [encode(child) for child in token.children] if token.children else None}


documents = {}
for name in NAMES:
    path = FOLDER / name
    original = path.read_text(encoding="utf-8")
    text = original.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", " - ")
    if name == NAMES[0]:
        text = re.sub(r"^## Contents\n.*?(?=^## 1\.)", "", text, flags=re.M | re.S)
    blocks, inline = [], []

    def block(match):
        blocks.append(match.group(1).strip())
        return f"\n\nNCBLOCKMATH{len(blocks)-1:03d}\n\n"

    def inside(match):
        inline.append(match.group(1).strip())
        return f"NCINLINEMATH{len(inline)-1:03d}"

    text = re.sub(r"\$\$(.*?)\$\$", block, text, flags=re.S)
    text = re.sub(r"\\\((.*?)\\\)", inside, text, flags=re.S)
    documents[name] = {"tokens": [encode(t) for t in parser.parse(text)],
                       "block_math": blocks, "inline_math": inline,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

(HERE / "parsed-documents.json").write_text(json.dumps(documents, ensure_ascii=False), encoding="utf-8")
print("Prepared all three reports, preserving their text, tables and mathematical expressions.")
