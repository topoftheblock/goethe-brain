"""Phase 1.1b - Fetch Goethe's works, letters, diaries and conversations from TextGrid.

Downloads the Goethe TEI corpora from https://textgridrep.org and flattens them into
plain-text files in data/raw/: one per work, or per year for letters, diaries
and conversations. Lines starting with "@@ " are section headings (a letter's
addressee, a poem's title, a chapter) that chunk.py prefixes to every chunk.

Texts are public domain; TextGrid's edition is CC BY 3.0 DE (TextGrid, www.editura.de).
"""
import json
import re
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
CACHE_DIR = RAW_DIR.parent / "tei_cache"
SOURCES_PATH = RAW_DIR / "textgrid_sources.json"
URL = "https://textgridlab.org/1.0/aggregator/teicorpus/textgrid:{}"
TEI = "{http://www.tei-c.org/ns/1.0}"

# name -> (TextGrid id, corpus depth that becomes one file, display title,
#          source_type, prefix headings with the file's year)
CORPORA = {
    "werke": ("11d7c.0", 2, "{} [German]", "primary", False),
    "briefe": ("11kbk.0", 1, "Goethes Briefe, {} [German]", "primary", True),
    "tagebuch": ("11chd.0", 1, "Goethes Tagebücher, {} [German]", "primary", True),
    "gespraeche": ("1237n.0", 1, "Goethes Gespräche, {} [German]", "conversation", False),
    # Science writings missing from "werke": the 1810 Farbenlehre vol. 1 (didactic and
    # polemical parts, original spelling) and two volumes of papers and drafts.
    "farbenlehre": ("4bhzs.0", 1, "{}, 1810 [German]", "primary", False),
    "naturschriften": ("4jt4d.0", 1, "{} [German]", "primary", False),
    "optik": ("4js6h.0", 1, "{} [German]", "primary", False),
}

# Skipped titles: editorial apparatus, and the part of the Farbenlehre that the
# complete 1810 volume ("farbenlehre") already contains.
SKIP = {
    "Biographie: Goethe, Johann Wolfgang", "[Zu den Tagebüchern]", "[Zu den Gesprächen]",
    "[Zu den Briefen]", "Verzeichnis abgekürzter oder inkorrekter Namen",
    "Personenverzeichnis", "Quellenverzeichnis", "Zur Farbenlehre. Didaktischer Teil",
}

LINE_TAGS = {"l", "speaker", "stage", "head", "closer", "row", "h3", "h4", "li", "tr", "br"}
PARA_TAGS = {"p", "lg", "sp", "div"}
DROP_TAGS = {"note", "front", "teiHeader", "fw"}


def squash(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "")


def render(el, unit: str, prefix: str) -> str:
    """Flatten a TEI element to text: one line per verse or speaker, a blank line per paragraph."""
    tag = el.tag.replace(TEI, "")
    if tag in DROP_TAGS:
        return ""
    out = squash(el.text) + "".join(render(child, unit, prefix) + squash(child.tail) for child in el)
    # zeno.org's table-of-contents path, e.g. ".../Wilhelm Meisters Lehrjahre/Erstes Buch/Erstes Kapitel"
    path = el.get("n", "").split("/")
    if tag == "div" and unit in path[:-1]:
        out = f"\n@@ {prefix}" + " — ".join(path[path.index(unit) + 1:]) + "\n" + out
    if tag in LINE_TAGS:
        return out + "\n"
    if tag in PARA_TAGS:
        return out + "\n\n"
    if tag == "lb":
        return "\v"  # a printed line break; convert() rejoins words hyphenated across it
    return out + " " if tag in ("cell", "td") else out


def iter_documents(path: Path):
    """Stream (titles of the enclosing corpora + the document's own, <TEI> element)."""
    titles = []
    for event, el in ET.iterparse(path, events=("start", "end")):
        tag = el.tag.replace(TEI, "")
        if event == "start" and tag in ("teiCorpus", "TEI"):
            titles.append(None)
        elif event == "end" and tag == "teiHeader" and titles[-1] is None:
            titles[-1] = squash(el.findtext(f".//{TEI}title")).strip()
        elif event == "end" and tag in ("teiCorpus", "TEI"):
            if tag == "TEI":
                yield titles[1:], el
            titles.pop()
            el.clear()


def download(name: str) -> Path:
    dest = CACHE_DIR / f"{name}.xml"
    if not dest.exists():
        CACHE_DIR.mkdir(exist_ok=True)
        print(f"Downloading {name} (slow, the letters take 20+ minutes) ...")
        part, _ = urllib.request.urlretrieve(URL.format(CORPORA[name][0]), dest.with_suffix(".part"))
        # The server streams without a Content-Length, so a dropped connection looks like success.
        if b"</teiCorpus>" not in Path(part).read_bytes()[-64:]:
            raise SystemExit(f"{name}: download was cut off, run again.")
        Path(part).rename(dest)
    return dest


def convert(name: str) -> dict[str, list]:
    _, depth, title_tpl, source_type, year_in_heading = CORPORA[name]
    files: dict[str, str] = {}
    for titles, tei in iter_documents(download(name)):
        if SKIP & set(titles[:depth + 1]):
            continue
        unit = titles[depth - 1]
        prefix = f"{unit} — " if year_in_heading else ""
        heading = " — ".join(t for t in dict.fromkeys(titles[depth:]) if t != unit)
        text = render(tei.find(f"{TEI}text"), unit, prefix)
        files[unit] = files.get(unit, "") + (f"\n@@ {prefix}{heading}\n" if heading else "") + text

    sources = {}
    for unit, text in files.items():
        text = re.sub(r"-\v *(?=[a-zäöüſ])", "", text)
        text = re.sub(r" *\v *", " ", text)
        for old, new in ("ſ", "s"), ("aͤ", "ä"), ("oͤ", "ö"), ("uͤ", "ü"):  # 1810 typography
            text = text.replace(old, new)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) < 300:  # a cross-reference stub pointing into Schiller's corpus
            continue
        slug = re.sub(r"[^a-z0-9]+", "_", unit.lower().translate(str.maketrans("äöüß", "aous"))).strip("_")
        filename = f"{name}_{slug[:60]}_de.txt"
        (RAW_DIR / filename).write_text(text + "\n", encoding="utf-8")
        sources[filename] = [title_tpl.format(unit), source_type, None]
    print(f"{name}: wrote {len(sources)} files")
    return sources


def main():
    if SOURCES_PATH.exists():  # drop the previous run's files
        for filename in json.loads(SOURCES_PATH.read_text(encoding="utf-8")):
            (RAW_DIR / filename).unlink(missing_ok=True)
            (RAW_DIR.parent / "processed" / filename).unlink(missing_ok=True)
    sources = {}
    for name in CORPORA:
        sources.update(convert(name))
    SOURCES_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
