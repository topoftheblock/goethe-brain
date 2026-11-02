"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { FACE_IMAGE, drawFace } from "@/lib/face";

export interface TalkingPortraitHandle {
  speak: (audioUrl: string) => Promise<void>;
  stop: () => void;
}

/**
 * Tischbein's "Goethe in der Campagna", animated: the loudness of the TTS audio
 * opens the jaw and lifts the brows, and he blinks now and then.
 */
const TalkingPortrait = forwardRef<TalkingPortraitHandle>((_props, ref) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = FACE_IMAGE;
    let raf = 0;
    let open = 0;
    let brow = 0;
    let nextBlink = performance.now() + 3000;
    const data = new Uint8Array(128);

    const frame = (now: number) => {
      const canvas = canvasRef.current;
      if (canvas && img.complete) {
        let level = 0;
        if (analyserRef.current) {
          analyserRef.current.getByteTimeDomainData(data);
          level = Math.sqrt(data.reduce((s, v) => s + ((v - 128) / 128) ** 2, 0) / data.length);
        }
        open += (Math.min(1, level * 5) - open) * 0.5;
        brow += (Math.min(1, level * 3) - brow) * 0.05;
        if (now > nextBlink + 160) nextBlink = now + 3000 + Math.random() * 3000;
        const blink = now > nextBlink ? Math.sin((Math.PI * (now - nextBlink)) / 160) : 0;

        if (canvas.width !== img.naturalWidth) {
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
        }
        drawFace(canvas.getContext("2d")!, img, { open, blink, brow });
      }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, []);

  useImperativeHandle(ref, () => ({
    speak: async (audioUrl: string) => {
      const audio = audioRef.current!;
      if (!analyserRef.current) {
        const ctx = new AudioContext();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        ctx.createMediaElementSource(audio).connect(analyser);
        analyser.connect(ctx.destination);
        analyserRef.current = analyser;
      }
      await (analyserRef.current.context as AudioContext).resume();
      audio.src = audioUrl;
      setIsSpeaking(true);
      try {
        await audio.play();
        await new Promise((resolve) => (audio.onended = resolve));
      } finally {
        setIsSpeaking(false);
      }
    },
    stop: () => {
      audioRef.current?.pause();
      setIsSpeaking(false);
    },
  }));

  return (
    <div className="mx-auto w-full max-w-[380px] select-none">
      <canvas
        ref={canvasRef}
        role="img"
        aria-label="Goethe in the Roman Campagna, by Johann Heinrich Wilhelm Tischbein, 1787"
        className="aspect-square w-full ring-1 ring-ink/40 ring-offset-4 ring-offset-paper outline outline-1 outline-offset-[6px] outline-rule"
      />
      <audio ref={audioRef} className="hidden" />
      <p className="mt-5 text-center text-xs uppercase tracking-widest text-faded">
        {isSpeaking ? "Goethe is speaking…" : "Goethe in der Campagna, 1787"}
      </p>
    </div>
  );
});

TalkingPortrait.displayName = "TalkingPortrait";

export default TalkingPortrait;
