import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'YT Shorts Studio | Automated AI YouTube-to-Shorts Platform',
  description:
    'Repurpose long YouTube videos into viral 9:16 Shorts with dynamic captions, powered by faster-whisper, Gemini 1.5 Flash, FFmpeg, and YouTube Data API v3.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className={`${inter.className} min-h-full flex flex-col bg-zinc-950 text-zinc-100 selection:bg-red-500 selection:text-white`}>
        {children}
      </body>
    </html>
  );
}
