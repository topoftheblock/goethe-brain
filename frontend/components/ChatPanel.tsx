"use client";

import { useRef, useState } from "react";
import { ChatTurn, fetchSpeechUrl, sendMessage } from "@/lib/api";
import { TalkingPortraitHandle } from "./TalkingPortrait";

interface DisplayMessage extends ChatTurn {
  sources?: string[];
}

const SUGGESTIONS = [
  "What is your view on the nature of colors?",
  "What do you think of smartphones?",
  "Can you write a Python script for me?",
];

export default function ChatPanel({
  portraitRef,
}: {
  portraitRef: React.RefObject<TalkingPortraitHandle | null>;
}) {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: "assistant",
      content:
        "Good day to you, traveler of a stranger century than mine. I am Goethe — ask me of poetry, of nature, of colour, or of the restless heart of Werther. What troubles or delights your mind?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    });
  };

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    setError(null);
    const history: ChatTurn[] = messages.map(({ role, content }) => ({ role, content }));
    const nextMessages: DisplayMessage[] = [...messages, { role: "user", content }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    scrollToBottom();

    try {
      const { reply, sources } = await sendMessage(content, history);
      setMessages((prev) => [...prev, { role: "assistant", content: reply, sources }]);
      scrollToBottom();

      if (voiceEnabled) {
        try {
          const url = await fetchSpeechUrl(reply);
          await portraitRef.current?.speak(url);
        } catch (err) {
          console.error("TTS failed", err);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-1 py-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow ${
                m.role === "user"
                  ? "bg-amber-700/90 text-amber-50"
                  : "bg-neutral-900/80 text-amber-100 border border-amber-900/40 font-serif"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                <p className="mt-2 text-[10px] uppercase tracking-wide text-amber-400/60">
                  Drawing on: {m.sources.join(", ")}
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-amber-900/40 bg-neutral-900/80 px-4 py-3 text-sm text-amber-200/70 font-serif italic">
              Goethe is composing a reply…
            </div>
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-800 bg-red-950/60 px-3 py-2 text-xs text-red-300">
            {error}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 pb-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSend(s)}
            disabled={loading}
            className="rounded-full border border-amber-800/50 px-3 py-1 text-xs text-amber-300/80 hover:bg-amber-900/30 disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 border-t border-amber-900/30 pt-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Write to Goethe…"
          className="flex-1 rounded-full border border-amber-800/40 bg-neutral-900/60 px-4 py-2 text-sm text-amber-50 placeholder:text-amber-100/30 focus:outline-none focus:ring-1 focus:ring-amber-600"
        />
        <label className="flex items-center gap-1 text-xs text-amber-200/60">
          <input
            type="checkbox"
            checked={voiceEnabled}
            onChange={(e) => setVoiceEnabled(e.target.checked)}
          />
          voice
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-amber-700 px-4 py-2 text-sm font-medium text-amber-50 hover:bg-amber-600 disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
