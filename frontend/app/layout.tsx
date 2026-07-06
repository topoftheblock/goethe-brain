import type { Metadata } from "next";
import { EB_Garamond, Cormorant_Garamond } from "next/font/google";
import "./globals.css";

const serif = EB_Garamond({
  variable: "--font-serif",
  subsets: ["latin"],
});

const display = Cormorant_Garamond({
  variable: "--font-display",
  weight: ["500", "600", "700"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Goethe AI — Speak with the Poet",
  description:
    "A RAG-powered conversational persona of Johann Wolfgang von Goethe, grounded in his own works.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${display.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-neutral-950 text-amber-50">{children}</body>
    </html>
  );
}
