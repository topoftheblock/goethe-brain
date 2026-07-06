export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  reply: string;
  sources: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function sendMessage(message: string, history: ChatTurn[]): Promise<ChatResult> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Chat request failed (${res.status}): ${body}`);
  }
  return res.json();
}

export async function fetchSpeechUrl(text: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`TTS request failed (${res.status}): ${body}`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
