"use client";

import { useRef } from "react";
import ChatPanel from "@/components/ChatPanel";
import TalkingPortrait, { TalkingPortraitHandle } from "@/components/TalkingPortrait";

export default function Home() {
  const portraitRef = useRef<TalkingPortraitHandle | null>(null);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 md:py-12">
      <header className="mb-8 text-center">
        <p className="font-display text-sm uppercase tracking-[0.3em] text-amber-500/70">
          A Portfolio Project
        </p>
        <h1 className="font-display mt-2 text-4xl font-semibold text-amber-100 md:text-5xl">
          Goethe AI
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-amber-200/60">
          A retrieval-augmented conversational persona of Johann Wolfgang von Goethe, grounded in{" "}
          <em>Faust</em>, <em>The Sorrows of Young Werther</em>, and the <em>Theory of Colours</em>.
          Speak with him below — he answers, and he speaks aloud.
        </p>
      </header>

      <div className="grid flex-1 grid-cols-1 gap-8 md:grid-cols-[minmax(280px,340px)_1fr]">
        <div className="flex flex-col items-center justify-start">
          <TalkingPortrait ref={portraitRef} />
        </div>
        <div className="min-h-[520px] rounded-2xl border border-amber-900/30 bg-neutral-950/60 p-4 shadow-xl md:min-h-[600px]">
          <ChatPanel portraitRef={portraitRef} />
        </div>
      </div>

      <footer className="mt-10 text-center text-xs text-amber-200/30">
        Source texts via Project Gutenberg (public domain). Portrait: Joseph Karl Stieler, 1828
        (Wikimedia Commons, public domain). This is an AI persona for demonstration purposes, not
        a historical record of Goethe&apos;s actual views.
      </footer>
    </main>
  );
}
