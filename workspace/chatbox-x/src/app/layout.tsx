import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Chatbox-X - Local Ollama AI',
  description: 'Clean Next.js chat application streaming from local Gemma 4 model via Ollama',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
