"""Phase 3.1 - Retrieval over the vector store."""
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


def retrieve(query: str, kind: str | None = None, top_k: int = config.RETRIEVAL_TOP_K) -> list[dict]:
    """Retrieve top-k passages, optionally of one source_type, at most two per work.

    The cap keeps one long, densely relevant source from crowding out the rest.
    """
    client = get_openai_client()
    embedding = client.embeddings.create(model=config.EMBEDDING_MODEL, input=[query]).data[0].embedding
    collection = get_collection()
    results = collection.query(
        query_embeddings=[embedding], n_results=top_k * 3, where={"source_type": kind} if kind else None
    )

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
