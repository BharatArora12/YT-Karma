'use client';

import React from 'react';
import { AlertCircle, CheckCircle2, Cpu, Sparkles, Terminal, Video } from 'lucide-react';
import { HealthStatus } from '../lib/types';

interface HealthBannerProps {
  health: HealthStatus | null;
}

export const SystemHealthBanner: React.FC<HealthBannerProps> = ({ health }) => {
  if (!health) {
    return (
      <div className="mb-6 p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 text-amber-300 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Connecting to FastAPI backend at <code className="bg-amber-500/20 px-1 py-0.5 rounded">http://localhost:8000</code>... Ensure the backend server is running.
          </span>
        </div>
      </div>
    );
  }

  const hasFfmpeg = health.ffmpeg.available;
  const hasGemini = health.gemini.configured;

  return (
    <div className="mb-8 space-y-3">
      {/* Notice if FFmpeg or Gemini needs attention */}
      {!hasFfmpeg && (
        <div className="p-3.5 rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-amber-200">
          <div className="flex items-center gap-2.5">
            <Video className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-semibold text-amber-300">FFmpeg executable not detected:</span>{' '}
              Video cropping &amp; dynamic captions require FFmpeg.
            </div>
          </div>
          <div className="flex items-center gap-2 font-mono text-[11px] bg-black/40 px-2.5 py-1 rounded-md border border-amber-500/20 text-amber-300">
            <Terminal className="w-3 h-3 text-amber-400" />
            <span>winget install Gyan.FFmpeg</span>
          </div>
        </div>
      )}

      {/* Pipeline Stack Micro-badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Core Ingestion */}
        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-red-500/10 text-red-400">
            <Video className="w-3.5 h-3.5" />
          </div>
          <div className="text-[11px] leading-tight">
            <div className="text-zinc-400">Step 1 Ingestion</div>
            <div className="text-zinc-200 font-medium">yt-dlp Engine</div>
          </div>
        </div>

        {/* Whisper */}
        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
            <Cpu className="w-3.5 h-3.5" />
          </div>
          <div className="text-[11px] leading-tight">
            <div className="text-zinc-400">Step 2 Whisper</div>
            <div className="text-zinc-200 font-medium">{health.whisper.model_size} ({health.whisper.compute_type})</div>
          </div>
        </div>

        {/* Gemini */}
        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div className="text-[11px] leading-tight">
            <div className="text-zinc-400">Step 3 AI Analysis</div>
            <div className="text-zinc-200 font-medium">
              {hasGemini ? 'Gemini 1.5 Flash' : 'Smart Heuristics'}
            </div>
          </div>
        </div>

        {/* FFmpeg */}
        <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg ${hasFfmpeg ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
            {hasFfmpeg ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
          </div>
          <div className="text-[11px] leading-tight">
            <div className="text-zinc-400">Step 4 FFmpeg</div>
            <div className={hasFfmpeg ? 'text-emerald-300 font-medium' : 'text-amber-300 font-medium'}>
              {hasFfmpeg ? '9:16 + .ass Subtitles' : 'Configure Path'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
