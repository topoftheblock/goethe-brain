"""Phase 3 - The agent loop: Goethe decides what to look up in his papers before he answers."""
import json

from app import config, persona, rag

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_papers",
        "description": "Search Goethe's works, letters, diaries and recorded conversations, "
        "and the biographies written about him.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to look for, worded as the passage itself might read. "
                    "In German, except for biographies, which are mostly English.",
                },
                "kind": {
                    "type": "string",
                    "enum": ["primary", "conversation", "biography"],
                    "description": "Optional filter: his own writings (works, letters, diaries), "
                    "records of his conversation, or biographies and essays about him.",
                },
            },
            "required": ["query"],
        },
    },
}


def reply(message: str, history: list[dict]) -> tuple[str, list[str]]:
    """Let the model search up to MAX_SEARCHES rounds, then answer. Returns (reply, sources used)."""
    client = rag.get_openai_client()
    messages = [{"role": "system", "content": persona.SYSTEM_PROMPT}, *history, {"role": "user", "content": message}]
    sources: set[str] = set()
    for round_ in range(config.MAX_SEARCHES + 1):
        completion = client.chat.completions.create(
            model=config.CHAT_MODEL,
            messages=messages,
            tools=[SEARCH_TOOL],
            tool_choice="auto" if round_ < config.MAX_SEARCHES else "none",
            temperature=0.8,
            max_tokens=400,
        )
        answer = completion.choices[0].message
        if not answer.tool_calls:
            return answer.content, sorted(sources)
        messages.append(answer)
        for call in answer.tool_calls:
            try:
                passages = rag.retrieve(**json.loads(call.function.arguments))
            except Exception:
                passages = []
            sources.update(p["source"] for p in passages)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": persona.format_passages(passages)})
