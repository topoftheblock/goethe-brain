"""Phase 2 - Embed chunks and load them into the local ChromaDB vector store."""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import chromadb
from openai import OpenAI

load_dotenv()

BACKEND_DIR = Path(__file__).parent.parent
CHUNKS_PATH = BACKEND_DIR / "data" / "processed" / "chunks.jsonl"
CHROMA_PATH = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "goethe_texts"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def load_chunks() -> list[dict]:
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in.")

    chunks = load_chunks()
    if not chunks:
        sys.exit(f"No chunks found at {CHUNKS_PATH}. Run clean.py and chunk.py first.")

    client = OpenAI(api_key=api_key)
    chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
    chroma.delete_collection(COLLECTION_NAME) if COLLECTION_NAME in [c.name for c in chroma.list_collections()] else None
    collection = chroma.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        embeddings = embed_batch(client, [c["text"] for c in batch])
        collection.add(
            ids=[c["id"] for c in batch],
            embeddings=embeddings,
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "source": c["source"],
                    "source_type": c.get("source_type", "primary"),
                    "author": c.get("author") or "",
                }
                for c in batch
            ],
        )
        print(f"Embedded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print(f"\nDone. Collection '{COLLECTION_NAME}' has {collection.count()} vectors at {CHROMA_PATH}")


if __name__ == "__main__":
    main()
