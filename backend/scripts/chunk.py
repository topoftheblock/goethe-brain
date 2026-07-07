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

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

SOURCE_TITLES = {
    "faust_part1.txt": "Faust, Part I",
    "werther.txt": "The Sorrows of Young Werther",
    "theory_of_colours.txt": "Theory of Colours",
    "poems_of_goethe.txt": "The Poems of Goethe",
    "autobiography.txt": "The Autobiography of Goethe (Poetry and Truth)",
    "maxims_and_reflections.txt": "Maxims and Reflections",
    "wilhelm_meister_vol1.txt": "Wilhelm Meister's Apprenticeship, Vol. I",
    "wilhelm_meister_vol2.txt": "Wilhelm Meister's Apprenticeship, Vol. II",
    "italian_journey_letters.txt": "Letters from Switzerland and Travels in Italy",
    # English
    "egmont_en.txt": "Egmont",
    "hermann_and_dorothea_en.txt": "Hermann and Dorothea",
    "erotica_romana_en.txt": "Erotica Romana",
    "iphigenia_in_tauris_en.txt": "Iphigenia in Tauris",
    "literary_essays_en.txt": "Goethe's Literary Essays",
    "xenions_en.txt": "Goethe and Schiller's Xenions",
    "princess_and_tiger_en.txt": "The Princess and the Tiger",
    # German (no English translation available on Gutenberg)
    "die_wahlverwandtschaften_de.txt": "Die Wahlverwandtschaften (Elective Affinities) [German]",
    "torquato_tasso_de.txt": "Torquato Tasso [German]",
    "goetz_von_berlichingen_de.txt": "Götz von Berlichingen [German]",
    "reineke_fuchs_de.txt": "Reineke Fuchs [German]",
    "wilhelm_meister_wanderjahre_vol1_de.txt": "Wilhelm Meisters Wanderjahre, Vol. I [German]",
    "wilhelm_meister_wanderjahre_vol2_de.txt": "Wilhelm Meisters Wanderjahre, Vol. II [German]",
    "wilhelm_meister_wanderjahre_vol3_de.txt": "Wilhelm Meisters Wanderjahre, Vol. III [German]",
    "west_oestlicher_divan_de.txt": "West-östlicher Divan [German]",
    "roemische_elegien_de.txt": "Römische Elegien [German]",
    "venetianische_epigramme_de.txt": "Venetianische Epigramme [German]",
    "die_natuerliche_tochter_de.txt": "Die natürliche Tochter [German]",
    "die_mitschuldigen_de.txt": "Die Mitschuldigen [German]",
    "prometheus_fragment_de.txt": "Prometheus: Dramatisches Fragment [German]",
    "die_geschwister_de.txt": "Die Geschwister [German]",
    "unterhaltungen_deutscher_ausgewanderten_de.txt": "Unterhaltungen deutscher Ausgewanderten [German]",
    "italienische_reise_vol1_de.txt": "Italienische Reise, Vol. I [German]",
    "italienische_reise_vol2_de.txt": "Italienische Reise, Vol. II [German]",
    "satyros_de.txt": "Satyros [German]",
    "die_laune_des_verliebten_de.txt": "Die Laune des Verliebten [German]",
    "die_aufgeregten_de.txt": "Die Aufgeregten [German]",
    "belagerung_von_mainz_de.txt": "Belagerung von Mainz [German]",
    "kampagne_in_frankreich_de.txt": "Kampagne in Frankreich [German]",
    # Letters
    "briefe_an_leipziger_freunde_de.txt": "Goethe's Letters to Leipzig Friends [German]",
    "briefe_an_auguste_zu_stolberg_de.txt": "Goethe's Letters to Auguste zu Stolberg [German]",
    "briefe_an_lavater_de.txt": "Goethe's Letters to Lavater, 1774-1783 [German]",
    "briefe_goethe_und_werther_de.txt": "Goethe and Werther: Goethe's Letters [German]",
    "briefe_schiller_goethe_an_schlegel_de.txt": "Schiller & Goethe's Letters to A. W. Schlegel [German]",
}

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    id: str
    source: str
    text: str


def _split(text: str, separators: list[str]) -> list[str]:
    if not separators:
        return [text]
    sep = separators[0]
    if sep == "":
        return [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    parts = text.split(sep) if sep else list(text)
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
        candidate = (current + "\n\n" + piece).strip() if current else piece
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
        else:
            if current:
                chunks.append(current)
                overlap_tail = current[-CHUNK_OVERLAP:]
                current = (overlap_tail + "\n\n" + piece).strip()
            else:
                current = piece
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c.strip()) > 40]


def main():
    all_chunks: list[Chunk] = []
    for src in sorted(CLEAN_DIR.glob("*.txt")):
        text = src.read_text(encoding="utf-8")
        title = SOURCE_TITLES.get(src.name, src.stem)
        pieces = recursive_chunk(text)
        for i, piece in enumerate(pieces):
            all_chunks.append(Chunk(id=f"{src.stem}-{i:05d}", source=title, text=piece))
        print(f"{title}: {len(pieces)} chunks")

    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    print(f"\nWrote {len(all_chunks)} total chunks to {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
