"""Phase 3.1/3.3 - Retrieval over the vector store, with short-term memory folded into the query."""
import chromadb
from openai import OpenAI

from app import config

_client: OpenAI | None = None
_collection = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        chroma = chromadb.PersistentClient(path=str(config.CHROMA_PATH))
        _collection = chroma.get_collection(config.COLLECTION_NAME)
    return _collection


def build_retrieval_query(user_message: str, history: list[dict]) -> str:
    """Compress the last few turns + the new message into one retrieval query.

    A lightweight stand-in for a dedicated 'condense question' LLM call: recent
    turns give the query conversational context without an extra round-trip.
    """
    recent = history[-(config.MEMORY_TURNS * 2):]
    recent_text = " ".join(turn["content"] for turn in recent)
    return f"{recent_text} {user_message}".strip()


def retrieve(query: str, top_k: int = config.RETRIEVAL_TOP_K) -> list[dict]:
    """Retrieve top-k passages, capping how many can come from the same work.

    With ~24,000 chunks spanning dozens of works, an unconstrained top-k can end
    up dominated by one long, densely-relevant source. A small per-source cap
    keeps answers grounded in a spread of works instead of just one.
    """
    client = get_openai_client()
    embedding = client.embeddings.create(model=config.EMBEDDING_MODEL, input=[query]).data[0].embedding
    collection = get_collection()
    results = collection.query(query_embeddings=[embedding], n_results=top_k * 3)

    passages = []
    per_source_count: dict[str, int] = {}
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = meta["source"]
        if per_source_count.get(source, 0) >= 2:
            continue
        passages.append(
            {
                "text": doc,
                "source": source,
                "source_type": meta.get("source_type", "primary"),
                "author": meta.get("author") or None,
            }
        )
        per_source_count[source] = per_source_count.get(source, 0) + 1
        if len(passages) >= top_k:
            break
    return passages
