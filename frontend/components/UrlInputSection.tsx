'use client';

import React, { useState } from 'react';
import { Sparkles, Sliders, ArrowRight, Loader2, PlaySquare } from 'lucide-react';
import { YouTubeIcon as Youtube } from './Icons';

interface UrlInputSectionProps {
  onSubmit: (url: string, clipCount: number, minDur: number, maxDur: number) => void;
  isLoading: boolean;
}

const SAMPLE_VIDEOS = [
  {
    title: 'Veritasium Science Demo',
    url: 'https://www.youtube.com/watch?v=bHIhgxav9LY',
  },
  {
    title: 'TED: 3 Secrets to Viral Ideas',
    url: 'https://www.youtube.com/watch?v=iCvmsMzlF7o',
  },
  {
    title: 'OpenAI Dev Day Keynote',
    url: 'https://www.youtube.com/watch?v=U9mJuUkhUzk',
  },
];

export const UrlInputSection: React.FC<UrlInputSectionProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [clipCount, setClipCount] = useState(3);
  const [minDuration, setMinDuration] = useState(30);
  const [maxDuration, setMaxDuration] = useState(60);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit(url.trim(), clipCount, minDuration, maxDuration);
  };

  const handleSelectSample = (sampleUrl: string) => {
    setUrl(sampleUrl);
  };

  return (
    <div className="relative rounded-2xl bg-gradient-to-b from-zinc-900 to-zinc-950 p-6 sm:p-8 border border-zinc-800 shadow-2xl shadow-red-950/10 overflow-hidden mb-8">
      {/* Decorative background glow */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none -z-0" />
      <div className="absolute -bottom-10 -left-10 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none -z-0" />

      <div className="relative z-10 max-w-3xl mx-auto text-center space-y-4">
        {/* Headline */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Automated 5-Step Repurposing Pipeline</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Turn Any Long YouTube Video Into{' '}
          <span className="bg-gradient-to-r from-red-500 via-rose-400 to-amber-400 bg-clip-text text-transparent">
            Viral YouTube Shorts
          </span>
        </h1>

        <p className="text-zinc-400 text-sm sm:text-base max-w-xl mx-auto">
          Ingest via <span className="text-zinc-200">yt-dlp</span>, transcribe with <span className="text-zinc-200">faster-whisper</span>, pick viral hooks with <span className="text-zinc-200">Gemini 1.5 Flash</span>, crop to 9:16 with <span className="text-zinc-200">FFmpeg</span>, and publish directly to your channel.
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5 p-2 rounded-2xl bg-zinc-950/80 border border-zinc-700/80 shadow-inner focus-within:border-red-500 focus-within:ring-2 focus-within:ring-red-500/20 transition-all">
            <div className="flex items-center pl-3 pr-2 text-zinc-400">
              <Youtube className="w-6 h-6 text-red-500 shrink-0" />
            </div>

            <input
              type="url"
              required
              placeholder="Paste YouTube Video URL (e.g., https://www.youtube.com/watch?v=...)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isLoading}
              className="w-full bg-transparent text-sm sm:text-base text-zinc-100 placeholder-zinc-500 focus:outline-none px-2 py-3"
            />

            <button
              type="submit"
              disabled={isLoading || !url.trim()}
              className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-600/25 active:scale-95 transition-all shrink-0"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>Generate Shorts</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Quick Samples & Options Toggle */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-zinc-400">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-zinc-400">Try Sample:</span>
              {SAMPLE_VIDEOS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectSample(s.url)}
                  disabled={isLoading}
                  className="px-2.5 py-1 rounded-md bg-zinc-800/80 hover:bg-zinc-700 hover:text-white border border-zinc-700/50 transition truncate max-w-[170px]"
                >
                  {s.title}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 transition"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showAdvanced ? 'Hide Options' : 'Pipeline Settings'}</span>
            </button>
          </div>

          {/* Advanced Settings Drawer */}
          {showAdvanced && (
            <div className="p-4 rounded-xl bg-zinc-950/90 border border-zinc-800 text-left grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-in fade-in duration-200">
              <div>
                <label className="block text-zinc-300 font-medium mb-1">
                  Target Shorts Count: <span className="text-red-400 font-bold">{clipCount}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={clipCount}
                  onChange={(e) => setClipCount(Number(e.target.value))}
                  className="w-full accent-red-500"
                />
                <span className="text-[10px] text-zinc-400">Generates 1 to 5 standalone clips</span>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">
                  Min Clip Duration: <span className="text-red-400 font-bold">{minDuration}s</span>
                </label>
                <input
                  type="range"
                  min="15"
                  max="45"
                  step="5"
                  value={minDuration}
                  onChange={(e) => setMinDuration(Number(e.target.value))}
                  className="w-full accent-red-500"
                />
                <span className="text-[10px] text-zinc-400">Minimum standalone segment</span>
              </div>

              <div>
                <label className="block text-zinc-300 font-medium mb-1">
                  Max Clip Duration: <span className="text-red-400 font-bold">{maxDuration}s</span>
                </label>
                <input
                  type="range"
                  min="45"
                  max="90"
                  step="5"
                  value={maxDuration}
                  onChange={(e) => setMaxDuration(Number(e.target.value))}
                  className="w-full accent-red-500"
                />
                <span className="text-[10px] text-zinc-400">Standard YouTube Shorts limit is 60s</span>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
