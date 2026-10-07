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
        "So, a visitor from a later century. Sit down, my good friend. Ask what you will: of poems, of plants and colours, of Italy, of the people I have known. What brings you to me?",
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
    <div className="flex h-full flex-col text-lg leading-relaxed">
      <div ref={scrollRef} className="flex-1 space-y-6 overflow-y-auto pb-6">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <p key={i} className="ml-auto max-w-[80%] whitespace-pre-wrap text-right italic text-faded">
              {m.content}
            </p>
          ) : (
            <div key={i} className="max-w-[90%] border-l-2 border-purpur/60 pl-4">
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                <p className="mt-2 text-xs text-faded">Aus: {m.sources.join(" · ")}</p>
              )}
            </div>
          ),
        )}
        {loading && (
          <p className="flex items-center gap-3 italic text-faded">
            <span className="farbenkreis size-4 animate-spin [animation-duration:4s] motion-reduce:animate-none" />
            Goethe considers…
          </p>
        )}
        {error && <p className="text-sm text-purpur">{error}</p>}
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1 pb-3 text-sm italic text-faded">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSend(s)}
            disabled={loading}
            className="underline decoration-rule underline-offset-4 hover:text-purpur disabled:opacity-40"
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
        className="flex items-center gap-4 border-t border-rule pt-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Write to Goethe…"
          aria-label="Your message to Goethe"
          className="flex-1 border-b border-ink/40 bg-transparent py-2 placeholder:italic placeholder:text-faded focus:border-purpur focus:outline-none"
        />
        <label className="flex items-center gap-1.5 text-sm text-faded">
          <input
            type="checkbox"
            checked={voiceEnabled}
            onChange={(e) => setVoiceEnabled(e.target.checked)}
            className="accent-purpur"
          />
          voice
        </label>
        <button
          type="submit"
          disabled={loading}
          className="font-display text-xl text-purpur hover:underline disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
