"use client";

import Image from "next/image";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

export interface TalkingPortraitHandle {
  speak: (audioUrl: string) => Promise<void>;
  stop: () => void;
}

/**
 * A lightweight "talking painting" effect: a static portrait with an
 * audio-reactive mouth overlay driven by the amplitude of whatever is
 * playing through the hidden <audio> element. Not a trained lip-sync
 * model — just enough motion to sell the illusion of speech for a demo.
 */
const TalkingPortrait = forwardRef<TalkingPortraitHandle>((_props, ref) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const [mouthOpen, setMouthOpen] = useState(0); // 0..1
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [blink, setBlink] = useState(false);

  useEffect(() => {
    const id = window.setInterval(() => {
      setBlink(true);
      window.setTimeout(() => setBlink(false), 140);
    }, 3800 + Math.random() * 2500);
    return () => window.clearInterval(id);
  }, []);

  const ensureGraph = () => {
    if (!audioRef.current) return;
    if (!audioCtxRef.current) {
      const ctx = new AudioContext();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      const source = ctx.createMediaElementSource(audioRef.current);
      source.connect(analyser);
      analyser.connect(ctx.destination);
      audioCtxRef.current = ctx;
      analyserRef.current = analyser;
      sourceRef.current = source;
    }
  };

  const tick = () => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);
    let sumSquares = 0;
    for (const v of data) {
      const norm = (v - 128) / 128;
      sumSquares += norm * norm;
    }
    const rms = Math.sqrt(sumSquares / data.length);
    setMouthOpen(Math.min(1, rms * 4.5));
    rafRef.current = requestAnimationFrame(tick);
  };

  useImperativeHandle(ref, () => ({
    speak: async (audioUrl: string) => {
      if (!audioRef.current) return;
      ensureGraph();
      await audioCtxRef.current?.resume();
      audioRef.current.src = audioUrl;
      setIsSpeaking(true);
      rafRef.current = requestAnimationFrame(tick);
      try {
        await audioRef.current.play();
        await new Promise<void>((resolve) => {
          if (!audioRef.current) return resolve();
          audioRef.current.onended = () => resolve();
        });
      } finally {
        setIsSpeaking(false);
        setMouthOpen(0);
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
      }
    },
    stop: () => {
      audioRef.current?.pause();
      setIsSpeaking(false);
      setMouthOpen(0);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    },
  }));

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      audioCtxRef.current?.close();
    };
  }, []);

  const mouthScaleY = 0.35 + mouthOpen * 1.65;

  return (
    <div className="relative w-full max-w-sm mx-auto select-none">
      <div className="relative aspect-[960/1184] w-full overflow-hidden rounded-lg shadow-2xl ring-1 ring-amber-900/40">
        <Image
          src="/images/goethe-portrait.jpg"
          alt="Portrait of Johann Wolfgang von Goethe by Joseph Karl Stieler, 1828"
          fill
          priority
          className="object-cover"
        />

        {/* eyelids */}
        <div
          className="absolute bg-[#c9a789] rounded-full origin-center transition-transform duration-75"
          style={{
            left: "37.5%",
            top: "23.3%",
            width: "7%",
            height: "1.6%",
            transform: `scaleY(${blink ? 1 : 0})`,
          }}
        />
        <div
          className="absolute bg-[#c9a789] rounded-full origin-center transition-transform duration-75"
          style={{
            left: "48.5%",
            top: "22.3%",
            width: "6.5%",
            height: "1.6%",
            transform: `scaleY(${blink ? 1 : 0})`,
          }}
        />

        {/* mouth */}
        <div
          className="absolute origin-center rounded-[50%] transition-transform duration-75 ease-out"
          style={{
            left: "43%",
            top: "33.6%",
            width: "9%",
            height: "1.8%",
            background:
              "radial-gradient(ellipse at center, #3a1712 0%, #6b2f22 60%, transparent 100%)",
            transform: `scaleY(${mouthScaleY})`,
            opacity: isSpeaking ? 0.9 : 0.5,
          }}
        />
      </div>

      <audio ref={audioRef} className="hidden" />

      <p className="mt-3 text-center text-xs uppercase tracking-widest text-amber-200/60">
        {isSpeaking ? "Goethe is speaking…" : "Johann Wolfgang von Goethe, 1828"}
      </p>
    </div>
  );
});

TalkingPortrait.displayName = "TalkingPortrait";

export default TalkingPortrait;
