# Goethe AI

A full-stack, retrieval-augmented conversational persona of **Johann Wolfgang von Goethe** —
grounded in his works, letters, diaries and recorded conversations: 310 source texts,
~110,000 chunks, split between his own writing (plays, novels, poetry, science writing, memoirs,
aphorisms, private letters) and what biographers, critics, and essayists have written *about* his
life and character. English where a translation exists, German original otherwise. Talk to him in
the browser; he answers in character — reading German sources as fluently as English ones, and
reacting to biographical accounts of himself as a real person would — and a lightweight
audio-reactive "talking portrait" animates while he speaks.

<details>
<summary>Full source list (310 texts, ~110,000 chunks)</summary>

**His own works, in English translation:**
Faust, Part I · The Sorrows of Young Werther · Theory of Colours · The Poems of Goethe ·
The Autobiography of Goethe (Poetry and Truth) · Maxims and Reflections ·
Wilhelm Meister's Apprenticeship (Vols. I–II) · Letters from Switzerland and Travels in Italy ·
Egmont · Hermann and Dorothea · Erotica Romana · Iphigenia in Tauris ·
Goethe's Literary Essays · Goethe and Schiller's Xenions · The Princess and the Tiger

**His own writings, German original (TextGrid Repository, see below):**
**Werke** — the collected works: *Faust* I and II, the *Urfaust*, the complete poems, the plays,
novels and tales, *Dichtung und Wahrheit*, *Italienische Reise*, *Tag- und Jahreshefte*, *Maximen
und Reflexionen*, some 45 essays on art and literature · **Science** — *Zur Farbenlehre*
(didactic, polemical and historical parts), the morphology and geology essays, and two volumes of
papers and drafts on osteology, optics and physics · **Briefe** — 13,000 letters 1764–1832, one
file per year, each headed with year and addressee · **Tagebücher** — the diaries 1775–1832 ·
**Gespräche** — Biedermann's edition of his recorded conversations (Eckermann, Kanzler von
Müller, Riemer, Soret and hundreds of visitors), each headed with date and partner · plus *Die
Geschwister* from Gutenberg

**Biographies and essays about him (by other authors):**
*Life of Johann Wolfgang Goethe* (James Sime) · *The Youth of Goethe* (P. Hume Brown) ·
*Representative Men* (Emerson, incl. his essay on Goethe) · *Three Philosophical Poets*
(Santayana, incl. chapter on Goethe) · *Three Essays* (Thomas Mann, incl. "Goethe and Tolstoy") ·
*Biographical Essays* (De Quincey, incl. essay on Goethe) · *Man or Matter* (Ernst Lehrs, on
Goethe's scientific worldview) · *The Three Devils* (David Masson, incl. essay on Goethe's
Mephistopheles) · *The Faust-Legend and Goethe's 'Faust'* (H. B. Cotterill) · *Kant und Goethe*
(Georg Simmel, German) · *Aus Goethes Frühzeit* (Wilhelm Scherer, German) · *J. W. v. Goethe's
Biographie* (Heinrich Döring, German) · *Goethes Lebenskunst* (Wilhelm Bode, German)

Each chunk is tagged `primary` (Goethe's own words), `conversation` (his talk as written down by
someone who was in the room) or `biography` (someone else's account of him) in the vector store's
metadata, and the persona prompt treats the three differently — quoting his own works directly,
recalling conversations as things he once said aloud, and reacting to biographical passages as a
real person hearing what history says about him ("I am told...").

Deliberately excluded: near-duplicate re-translations of works already covered (e.g. three other
English Faust Part I translations), anthologies where Goethe is a minor contributor among other
authors, and fictionalized "historical romance" novels about him rather than factual biography.
</details>

Built end-to-end from [`Goethe_AI_Agenda.md`](./Goethe_AI_Agenda.md).

## How it works

```
frontend (Next.js) --/api/chat--> backend (FastAPI) --> agent loop (gpt-4o-mini as Goethe)
                                                          |  ^
                                    search_papers(query,  |  |  passages, labelled as his own
                                    kind) — up to 3 rounds v  |  writing / conversation / biography
                                                        ChromaDB (local vector store)
       <------------- reply + sources -------------
       |
       +--/api/tts--> OpenAI TTS (tts-1) --> mp3 --> <audio> --> AnalyserNode drives the portrait's mouth
```

- **Data pipeline** (`backend/scripts/`): downloads (Gutenberg by hand, TextGrid via
  `fetch_textgrid.py`) → cleans Gutenberg boilerplate/footnotes →
  recursively chunks (~700 chars, 100 char overlap) → embeds with `text-embedding-3-small` →
  stores in a local persistent ChromaDB collection.
- **Agent** (`backend/app/agent.py`): one agent, one tool. Goethe himself decides whether to
  consult his papers and writes the search queries (in German, since most of the corpus is),
  optionally restricted to his own writing, his recorded conversations or the biographies. He may
  search up to three rounds, then must answer. Small talk costs no search at all.
- **Talking portrait** (`frontend/components/TalkingPortrait.tsx`): a static 1828 portrait
  (Joseph Karl Stieler, public domain) with an SVG-style mouth overlay whose vertical scale is
  driven live by the amplitude of the TTS audio via `AnalyserNode`. This is intentionally a
  cheap, dependency-free effect — not a trained lip-sync/video model — chosen so the demo needs
  no third-party video API or GPU.

## Project layout

```
backend/
  data/raw/            source texts (Project Gutenberg, downloaded)
  data/processed/      cleaned text + chunks.jsonl (generated)
  chroma_db/           persistent vector store (generated)
  data/tei_cache/      TextGrid TEI downloads (generated, ~500 MB, gitignored)
  scripts/
    fetch_textgrid.py  Phase 1.1b — download + flatten the TextGrid Goethe corpora
    clean.py           Phase 1.2 — strip Gutenberg headers/footers/footnotes
    chunk.py           Phase 1.3 — recursive character chunking
    ingest.py          Phase 2   — embed chunks + load into ChromaDB
  app/
    config.py
    agent.py           Phase 3   — the search-then-answer loop
    persona.py         Phase 3.2 — system prompt
    rag.py             Phase 3.1 — retrieval
    main.py            FastAPI app: /api/chat, /api/tts, /api/health
frontend/
  app/                 Next.js App Router pages
  components/
    ChatPanel.tsx
    TalkingPortrait.tsx
  lib/api.ts
```

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# one-time data pipeline (source texts are already in data/raw/)
python scripts/clean.py
python scripts/chunk.py
python scripts/ingest.py     # embeds ~110,000 chunks — roughly $0.50, takes a while

uvicorn app.main:app --reload --port 8000
```

Check `http://localhost:8000/api/health` — it should report `vectors_indexed` > 0 once ingestion
has run.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Re-running the data pipeline

If you add more Goethe texts, drop cleaned `.txt` files into `backend/data/raw/`, then re-run
`clean.py`, `chunk.py`, and `ingest.py` in order. `ingest.py` recreates the collection from
scratch each time, so it's always safe to re-run.

### The TextGrid corpora

The German works, letters, diaries and conversations come from the
[TextGrid Repository](https://textgridrep.org) (public-domain texts, edition CC BY 3.0 DE):

```bash
python scripts/fetch_textgrid.py
```

It downloads seven TEI corpora once into `data/tei_cache/` (the letters stream for 20+ minutes)
and writes plain-text files plus `textgrid_sources.json` (their titles) into `data/raw/`. Lines
starting with `@@ ` are section headings, which `chunk.py` prefixes to each chunk, e.g.
`[1823, 10. Juni. Mit Johann Peter Eckermann]`.

## Evaluation (Phase 5 test cases)

- **Direct knowledge**: "What is your view on the nature of colors?" → should draw on *Theory of
  Colours* and argue against Newton's optics.
- **Out of bounds**: "What do you think of smartphones?" → an in-character, wry deflection.
- **The trap**: "Can you write a Python script for me?" → a poetic, in-character refusal.

These three are wired up as one-click suggestion chips in the chat UI.

## Notes on the "deepfake"

There is no real audio/video of Goethe (he died in 1832) to train a voice-cloning or
lip-sync model on, and doing so would be neither possible nor appropriate. Instead this project
uses a synthetic TTS voice plus a real-time, audio-reactive animation overlaid on a public-domain
portrait — a transparent, low-cost stand-in for the "talking historical figure" effect, clearly
presented as an AI recreation for portfolio/demo purposes (see the footer disclaimer in the UI).
