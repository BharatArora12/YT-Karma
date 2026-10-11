'use client';

import React from 'react';
import { Sparkles, CheckCircle, AlertTriangle, RefreshCw, Radio } from 'lucide-react';
import { YouTubeIcon as Youtube } from './Icons';
import { HealthStatus } from '../lib/types';
import { getAuthUrl } from '../lib/api';

interface NavbarProps {
  health: HealthStatus | null;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ health, onRefreshHealth }) => {
  const [connecting, setConnecting] = React.useState(false);

  const handleConnectGoogle = async () => {
    try {
      setConnecting(true);
      const url = await getAuthUrl();
      window.location.href = url;
    } catch (e) {
      alert('Failed to initialize Google OAuth: ' + (e as Error).message);
      setConnecting(false);
    }
  };

  const isAuthed = health?.youtube_oauth?.authenticated;
  const channelName = health?.youtube_oauth?.channel_title;

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 via-rose-500 to-amber-500 shadow-lg shadow-red-500/25 ring-1 ring-white/20">
            <Youtube className="w-5 h-5 text-white fill-white" />
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-zinc-950 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                YT Shorts Studio
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                v1.0 Pro
              </span>
            </div>
            <p className="text-xs text-zinc-400 hidden sm:block">
              AI YouTube-to-Shorts Repurposing &amp; Publishing Engine
            </p>
          </div>
        </div>

        {/* Status Indicators & YouTube Auth */}
        <div className="flex items-center gap-3">
          {/* Health Pill */}
          <div
            onClick={onRefreshHealth}
            title={health ? `FFmpeg: ${health.ffmpeg.available ? 'Ready' : 'Missing'} | Gemini: ${health.gemini.configured ? 'Configured' : 'Fallback Heuristics'}` : 'Checking backend...'}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs bg-zinc-900 border border-zinc-800 text-zinc-300 cursor-pointer hover:border-zinc-700 transition"
          >
            <Radio className={`w-3.5 h-3.5 ${health ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
            <span className="hidden md:inline font-medium">Backend:</span>
            <span className={health ? 'text-emerald-400' : 'text-amber-400'}>
              {health ? 'Online' : 'Connecting...'}
            </span>
          </div>

          {/* YouTube Channel Connect */}
          {isAuthed ? (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-zinc-900/90 border border-red-500/30 text-xs shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <Youtube className="w-3.5 h-3.5 text-red-500 fill-red-500" />
              <span className="text-zinc-200 font-medium truncate max-w-[140px]">
                {channelName || 'YouTube Connected'}
              </span>
            </div>
          ) : (
            <button
              onClick={handleConnectGoogle}
              disabled={connecting}
              className="group flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium text-white bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-md shadow-red-600/20 active:scale-95 transition"
            >
              <Youtube className="w-3.5 h-3.5 fill-white text-white group-hover:scale-110 transition-transform" />
              <span>{connecting ? 'Connecting...' : 'Connect YouTube'}</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
