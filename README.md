# Goethe AI

A full-stack, retrieval-augmented conversational persona of **Johann Wolfgang von Goethe** —
grounded in essentially everything by Goethe available on Project Gutenberg: 43 source texts
covering his major plays, novels, poetry, science writing, memoirs, aphorisms, and private
letters, in both English translation and (where no English translation exists) the German
original. Talk to him in the browser; he answers in character — reading German sources as
fluently as English ones — and a lightweight audio-reactive "talking portrait" animates while he
speaks.

<details>
<summary>Full source list (43 texts, ~24,000 chunks)</summary>

**English translations:**
Faust, Part I · The Sorrows of Young Werther · Theory of Colours · The Poems of Goethe ·
The Autobiography of Goethe (Poetry and Truth) · Maxims and Reflections ·
Wilhelm Meister's Apprenticeship (Vols. I–II) · Letters from Switzerland and Travels in Italy ·
Egmont · Hermann and Dorothea · Erotica Romana · Iphigenia in Tauris ·
Goethe's Literary Essays · Goethe and Schiller's Xenions · The Princess and the Tiger

**German originals (no English translation on Gutenberg):**
Die Wahlverwandtschaften (Elective Affinities) · Torquato Tasso · Götz von Berlichingen ·
Reineke Fuchs · Wilhelm Meisters Wanderjahre (Vols. I–III) · West-östlicher Divan ·
Römische Elegien · Venetianische Epigramme · Die natürliche Tochter · Die Mitschuldigen ·
Prometheus (fragment) · Die Geschwister · Unterhaltungen deutscher Ausgewanderten ·
Italienische Reise (Vols. I–II) · Satyros · Die Laune des Verliebten · Die Aufgeregten ·
Belagerung von Mainz · Kampagne in Frankreich

**Letters (German, no English translation on Gutenberg):**
Letters to Leipzig friends · Letters to Auguste zu Stolberg · Letters to Lavater (1774–1783) ·
Letters exchanged with Charlotte Kestner around *Werther* · Schiller & Goethe's letters to
A. W. Schlegel

Deliberately excluded: near-duplicate re-translations of works already covered (e.g. three other
English Faust Part I translations), anthologies where Goethe is a minor contributor among other
authors, and books *about* Goethe rather than *by* him.
</details>

Built end-to-end from [`Goethe_AI_Agenda.md`](./Goethe_AI_Agenda.md).

## How it works

```
frontend (Next.js)  --/api/chat-->  backend (FastAPI)  --embed query-->  ChromaDB (local vector store)
       |                                   |                                   |
       |                              persona prompt +                   top-k passages from
       |                              retrieved passages                 Faust / Werther / Theory
       |                                   |                              of Colours
       |                                   v
       |                          OpenAI chat completion (gpt-4o-mini)
       |                                   |
  <----+---------------- reply -------------
       |
       +--/api/tts--> OpenAI TTS (tts-1) --> mp3 --> <audio> element
                                                          |
                                              Web Audio AnalyserNode reads
                                              amplitude in real time and
                                              drives the portrait's mouth
```

- **Data pipeline** (`backend/scripts/`): downloads → cleans Gutenberg boilerplate/footnotes →
  recursively chunks (~700 chars, 100 char overlap) → embeds with `text-embedding-3-small` →
  stores in a local persistent ChromaDB collection.
- **RAG + persona** (`backend/app/`): each chat turn folds the last few turns + the new message
  into one retrieval query, pulls the top-k passages, and injects them into a Goethe persona
  system prompt before calling the OpenAI chat model.
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
  scripts/
    clean.py           Phase 1.2 — strip Gutenberg headers/footers/footnotes
    chunk.py           Phase 1.3 — recursive character chunking
    ingest.py          Phase 2   — embed chunks + load into ChromaDB
  app/
    config.py
    persona.py         Phase 3.2 — system prompt
    rag.py             Phase 3.1/3.3 — retrieval + short-term memory
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
python scripts/ingest.py     # embeds ~24,000 chunks — roughly $0.10-0.20, takes several minutes

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
