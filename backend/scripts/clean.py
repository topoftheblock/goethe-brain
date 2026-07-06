"""Phase 1.2 - Text Data Cleaning.

Strips Project Gutenberg license headers/footers, illustration markers,
footnote blocks, and normalizes whitespace so the RAG pipeline only ever
sees Goethe's actual prose/verse.
"""
import re
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
CLEAN_DIR = Path(__file__).parent.parent / "data" / "processed"

START_RE = re.compile(r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE)
END_RE = re.compile(r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE)

NOISE_LINE_PATTERNS = [
    re.compile(r"^\[Illustration.*?\]$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$"),  # bare page numbers
    re.compile(r"^\[Footnote \d+.*?\]$", re.IGNORECASE),
    re.compile(r"^Produced by.*$", re.IGNORECASE),
    re.compile(r"^Transcriber('s)? [Nn]ote.*$"),
]


def strip_gutenberg_wrapper(text: str) -> str:
    start_match = START_RE.search(text)
    end_match = END_RE.search(text)
    if start_match and end_match:
        return text[start_match.end():end_match.start()]
    return text


def strip_noise_lines(text: str) -> str:
    lines = text.splitlines()
    kept = []
    for line in lines:
        stripped = line.strip()
        if any(p.match(stripped) for p in NOISE_LINE_PATTERNS):
            continue
        kept.append(line)
    return "\n".join(kept)


def collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = strip_gutenberg_wrapper(raw)
    text = strip_noise_lines(text)
    text = collapse_whitespace(text)
    return text


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(RAW_DIR.glob("*.txt")):
        cleaned = clean_file(src)
        out_path = CLEAN_DIR / src.name
        out_path.write_text(cleaned, encoding="utf-8")
        print(f"Cleaned {src.name}: {len(cleaned):,} chars (raw: {len(src.read_text(errors='ignore')):,})")


if __name__ == "__main__":
    main()
