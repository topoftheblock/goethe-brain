"""Phase 1.3 - Document Chunking Strategy.

A recursive character text splitter: split on paragraph breaks first,
falling back to sentence breaks, then raw characters, so chunks stay
close to the target size without cutting sentences awkwardly. Adjacent
chunks share a character overlap so meaning at the boundary is not lost.
"""
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict

CLEAN_DIR = Path(__file__).parent.parent / "data" / "processed"
CHUNKS_PATH = CLEAN_DIR / "chunks.jsonl"
# Titles for the files written by fetch_textgrid.py (same shape as SOURCE_META).
TEXTGRID_SOURCES_PATH = CLEAN_DIR.parent / "raw" / "textgrid_sources.json"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

# Each entry: filename -> (display title, "primary" [written by Goethe],
# "conversation" [his talk as written down by people who were present] or
# "biography" [written about Goethe by someone else], author for biography sources)
SOURCE_META: dict[str, tuple[str, str, str | None]] = {
    "faust_part1.txt": ("Faust, Part I", "primary", None),
    "werther.txt": ("The Sorrows of Young Werther", "primary", None),
    "theory_of_colours.txt": ("Theory of Colours", "primary", None),
    "poems_of_goethe.txt": ("The Poems of Goethe", "primary", None),
    "autobiography.txt": ("The Autobiography of Goethe (Poetry and Truth)", "primary", None),
    "maxims_and_reflections.txt": ("Maxims and Reflections", "primary", None),
    "wilhelm_meister_vol1.txt": ("Wilhelm Meister's Apprenticeship, Vol. I", "primary", None),
    "wilhelm_meister_vol2.txt": ("Wilhelm Meister's Apprenticeship, Vol. II", "primary", None),
    "italian_journey_letters.txt": ("Letters from Switzerland and Travels in Italy", "primary", None),
    # English
    "egmont_en.txt": ("Egmont", "primary", None),
    "hermann_and_dorothea_en.txt": ("Hermann and Dorothea", "primary", None),
    "erotica_romana_en.txt": ("Erotica Romana", "primary", None),
    "iphigenia_in_tauris_en.txt": ("Iphigenia in Tauris", "primary", None),
    "literary_essays_en.txt": ("Goethe's Literary Essays", "primary", None),
    "xenions_en.txt": ("Goethe and Schiller's Xenions", "primary", None),
    "princess_and_tiger_en.txt": ("The Princess and the Tiger", "primary", None),
    # German (no English translation available on Gutenberg)
    "die_geschwister_de.txt": ("Die Geschwister [German]", "primary", None),
    # Biographies, memoirs by others, and critical essays about Goethe the person
    "biography_sime_en.txt": ("Life of Johann Wolfgang Goethe", "biography", "James Sime"),
    "youth_of_goethe_en.txt": ("The Youth of Goethe", "biography", "P. Hume Brown"),
    "representative_men_emerson_en.txt": ("Representative Men (incl. essay on Goethe)", "biography", "Ralph Waldo Emerson"),
    "three_philosophical_poets_santayana_en.txt": ("Three Philosophical Poets (incl. chapter on Goethe)", "biography", "George Santayana"),
    "three_essays_thomasmann_en.txt": ("Three Essays (incl. 'Goethe and Tolstoy')", "biography", "Thomas Mann"),
    "biographical_essays_dequincey_en.txt": ("Biographical Essays (incl. essay on Goethe)", "biography", "Thomas De Quincey"),
    "man_or_matter_lehrs_en.txt": ("Man or Matter (on Goethe's approach to nature)", "biography", "Ernst Lehrs"),
    "three_devils_masson_en.txt": ("The Three Devils (incl. essay on Goethe's Mephistopheles)", "biography", "David Masson"),
    "faust_legend_cotterill_en.txt": ("The Faust-Legend and Goethe's 'Faust'", "biography", "H. B. Cotterill"),
    "kant_und_goethe_simmel_de.txt": ("Kant und Goethe [German]", "biography", "Georg Simmel"),
    "aus_goethes_fruehzeit_scherer_de.txt": ("Aus Goethes Frühzeit [German]", "biography", "Wilhelm Scherer"),
    "goethe_biographie_doering_de.txt": ("J. W. v. Goethe's Biographie [German]", "biography", "Heinrich Döring"),
    "goethes_lebenskunst_bode_de.txt": ("Goethes Lebenskunst [German]", "biography", "Wilhelm Bode"),
}

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    id: str
    source: str
    text: str
    source_type: str = "primary"
    author: str | None = None


def _split(text: str, separators: list[str]) -> list[str]:
    if not separators:
        return [text]
    sep = separators[0]
    if sep == "":
        return [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    # Keep each separator on the piece it ends, so re-joining pieces restores
    # the original text (sentence-final periods included).
    parts = [part + sep for part in text.split(sep)]
    parts[-1] = parts[-1][:-len(sep)]
    pieces = []
    for part in parts:
        if len(part) > CHUNK_SIZE:
            pieces.extend(_split(part, separators[1:]))
        elif part.strip():
            pieces.append(part)
    return pieces


def recursive_chunk(text: str) -> list[str]:
    """Merge small pieces up to CHUNK_SIZE, carrying CHUNK_OVERLAP chars forward."""
    pieces = _split(text, SEPARATORS)
    chunks = []
    current = ""
    for piece in pieces:
        candidate = current + piece
        if len(candidate.strip()) <= CHUNK_SIZE:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())
                current = current[-CHUNK_OVERLAP:] + piece
            else:
                current = piece
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if len(c) > 40]


def chunk_document(text: str) -> list[str]:
    """Chunk each "@@ heading" section on its own and prefix its chunks with the heading."""
    parts = re.split(r"^@@ (.*)\n", text, flags=re.MULTILINE)  # [body, heading, body, ...]
    pieces = recursive_chunk(parts[0])
    for heading, body in zip(parts[1::2], parts[2::2]):
        pieces += [f"[{heading}]\n{piece}" for piece in recursive_chunk(body)]
    return pieces


def main():
    all_chunks: list[Chunk] = []
    source_meta = dict(SOURCE_META)
    if TEXTGRID_SOURCES_PATH.exists():
        source_meta |= json.loads(TEXTGRID_SOURCES_PATH.read_text(encoding="utf-8"))
    for src in sorted(CLEAN_DIR.glob("*.txt")):
        text = src.read_text(encoding="utf-8")
        title, source_type, author = source_meta.get(src.name, (src.stem, "primary", None))
        pieces = chunk_document(text)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                Chunk(id=f"{src.stem}-{i:05d}", source=title, text=piece, source_type=source_type, author=author)
            )
        print(f"[{source_type}] {title}: {len(pieces)} chunks")

    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    print(f"\nWrote {len(all_chunks)} total chunks to {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
