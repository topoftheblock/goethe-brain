"use client";

import { useRef } from "react";
import ChatPanel from "@/components/ChatPanel";
import TalkingPortrait, { TalkingPortraitHandle } from "@/components/TalkingPortrait";

export default function Home() {
  const portraitRef = useRef<TalkingPortraitHandle | null>(null);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-5 py-8 md:py-12">
      <header className="mb-10 border-b border-rule pb-6 text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-faded">Weimar · am Frauenplan</p>
        <h1 className="font-display mt-3 flex items-center justify-center gap-4 text-5xl md:text-6xl">
          <span className="farbenkreis size-5" aria-hidden />
          Goethe
          <span className="farbenkreis size-5" aria-hidden />
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-pretty italic text-faded">
          A conversation with the poet in his last years, drawn from his works, thirteen thousand
          letters, his diaries and the talk his visitors wrote down.
        </p>
      </header>

      <div className="grid flex-1 grid-cols-1 gap-10 md:grid-cols-[minmax(220px,280px)_1fr]">
        <TalkingPortrait ref={portraitRef} />
        <div className="min-h-[520px] md:min-h-[600px]">
          <ChatPanel portraitRef={portraitRef} />
        </div>
      </div>

      <footer className="mt-12 border-t border-rule pt-4 text-center text-xs text-faded">
        Texts: TextGrid Repository and Project Gutenberg (public domain). Portrait: Joseph Karl
        Stieler, 1828 (Wikimedia Commons, public domain). An AI persona for demonstration, not a
        record of Goethe&apos;s actual views.
      </footer>
    </main>
  );
}
