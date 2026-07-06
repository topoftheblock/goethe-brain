import io

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import config, persona, rag

app = FastAPI(title="Goethe AI", description="A RAG-powered conversational persona of J. W. von Goethe")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []


class ChatResponse(BaseModel):
    reply: str
    sources: list[str]


class TTSRequest(BaseModel):
    text: str


@app.get("/api/health")
def health():
    try:
        count = rag.get_collection().count()
    except Exception:
        count = None
    return {"status": "ok", "vectors_indexed": count}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not config.OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY is not configured on the server.")
    if not req.message.strip():
        raise HTTPException(400, "message must not be empty")

    history = [turn.model_dump() for turn in req.history[-(config.MEMORY_TURNS * 2):]]
    query = rag.build_retrieval_query(req.message, history)

    try:
        passages = rag.retrieve(query)
    except Exception:
        passages = []

    messages = persona.build_messages(req.message, history, passages)

    client = rag.get_openai_client()
    completion = client.chat.completions.create(
        model=config.CHAT_MODEL,
        messages=messages,
        temperature=0.8,
        max_tokens=400,
    )
    reply = completion.choices[0].message.content

    sources = sorted({p["source"] for p in passages})
    return ChatResponse(reply=reply, sources=sources)


@app.post("/api/tts")
def tts(req: TTSRequest):
    if not config.OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY is not configured on the server.")
    if not req.text.strip():
        raise HTTPException(400, "text must not be empty")

    client = rag.get_openai_client()
    response = client.audio.speech.create(
        model=config.TTS_MODEL,
        voice=config.TTS_VOICE,
        input=req.text,
    )
    audio_bytes = response.read()
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
