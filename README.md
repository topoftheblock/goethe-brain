<div align="center">

# Goethe AI

**Talk to Johann Wolfgang von Goethe — grounded in 310 texts by and about him, voiced by AI, and painted by Tischbein.**

![Python](https://img.shields.io/badge/Python-FastAPI-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini%20%C2%B7%20TTS-412991?logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-110k%20chunks-FF6F00)

<img src="docs/desktop.jpg" alt="The Goethe AI chat: Tischbein's painting on the left, the conversation on the right" width="900">

</div>

A full-stack, retrieval-augmented conversational persona of Goethe, built from his works, letters,
diaries and recorded conversations, plus what biographers and critics wrote *about* him. English
where a translation exists, German original otherwise. He answers in character: he quotes his own
writing, recalls what he once said aloud, and reacts to biographies of himself as a real person
would. While he speaks, his face in Tischbein's *Goethe in der Campagna* moves with his AI voice.

## Highlights

- **Agentic RAG**: Goethe decides himself whether to consult his papers, and writes his own
  search queries, in German, over ~110,000 chunks.
- **Three kinds of source**: his own words, conversations others wrote down, and biographies are
  labelled separately, and he treats each one differently.
- **A talking painting**: the 1787 canvas is warped live from the loudness of the speech. The jaw
  opens, the brows lift and he blinks. No video model and no GPU.
- **Memory**: he remembers the last 20 exchanges, and the browser keeps the conversation.

<table>
  <tr>
    <td align="center"><img src="docs/talking.gif" alt="Goethe's painted face speaking and blinking" width="360"></td>
    <td align="center"><img src="docs/mobile.jpg" alt="The chat on a phone" width="240"></td>
  </tr>
  <tr>
    <td align="center"><sub>The painted face, animated by <code>frontend/lib/face.ts</code></sub></td>
    <td align="center"><sub>On a phone</sub></td>
  </tr>
</table>

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
       +--/api/tts--> OpenAI TTS (tts-1) --> mp3 --> <audio> --> AnalyserNode drives the painted face
```

- **Data pipeline** (`backend/scripts/`): downloads (Gutenberg by hand, TextGrid via
  `fetch_textgrid.py`) → cleans Gutenberg boilerplate/footnotes →
  recursively chunks (~700 chars, 100 char overlap) → embeds with `text-embedding-3-small` →
  stores in a local persistent ChromaDB collection.
- **Agent** (`backend/app/agent.py`): one agent, one tool. Goethe himself decides whether to
  consult his papers and writes the search queries (in German, since most of the corpus is),
  optionally restricted to his own writing, his recorded conversations or the biographies. He may
  search up to three rounds, then must answer. Small talk costs no search at all.
- **Memory**: he sees the last 20 exchanges (`MEMORY_TURNS`); the browser keeps the conversation
  in `localStorage` until "Begin anew".
- **Talking portrait** (`frontend/components/TalkingPortrait.tsx`, `frontend/lib/face.ts`):
  Tischbein's *Goethe in der Campagna* (1787, Städel Museum, public domain), drawn on a canvas.
  The loudness of the TTS audio (`AnalyserNode`) opens his jaw and lifts his brows by warping the
  painting itself, column by column; he blinks now and then. No video model, no GPU.

## Project layout

```
backend/
  data/raw/            source texts (Project Gutenberg + flattened TextGrid)
  data/processed/      cleaned text + chunks.jsonl (generated)
  data/tei_cache/      TextGrid TEI downloads (generated, ~500 MB, gitignored)
  chroma_db/           persistent vector store (generated)
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
  lib/
    api.ts
    face.ts            facial features of the painting + the warp
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

## A note on the "deepfake"

There is no real audio/video of Goethe (he died in 1832) to train a voice-cloning or
lip-sync model on, and doing so would be neither possible nor appropriate. Instead this project
uses a synthetic TTS voice and animates a public-domain painting in real time from that voice's
loudness — a transparent, low-cost stand-in for the "talking historical figure" effect, clearly
presented as an AI recreation for portfolio/demo purposes (see the footer disclaimer in the UI).

## Credits

- Texts: [TextGrid Repository](https://textgridrep.org) (CC BY 3.0 DE) and
  [Project Gutenberg](https://www.gutenberg.org) (public domain).
- Painting: Johann Heinrich Wilhelm Tischbein, *Goethe in der Campagna*, 1787, Städel Museum,
  Frankfurt am Main (public domain, via
  [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Goethe_in_the_Roman_Campagna_(SM_1157).png)).
