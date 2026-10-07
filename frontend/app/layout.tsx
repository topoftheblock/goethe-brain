import type { Metadata } from "next";
import { EB_Garamond, Bodoni_Moda } from "next/font/google";
import "./globals.css";

const serif = EB_Garamond({
  variable: "--font-serif",
  subsets: ["latin"],
});

// A Didone in the manner of Walbaum, who cut his types in Goethe's Weimar.
const display = Bodoni_Moda({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Goethe — A Conversation in Weimar",
  description:
    "Talk with Johann Wolfgang von Goethe, an AI persona grounded in his works, letters, diaries and recorded conversations.",
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
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
