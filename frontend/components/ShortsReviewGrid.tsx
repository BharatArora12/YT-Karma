'use client';

import React from 'react';
import { Film, Sparkles, SlidersHorizontal, RefreshCw } from 'lucide-react';
import { ShortClip } from '../lib/types';
import { ShortCard } from './ShortCard';

interface ShortsReviewGridProps {
  clips: ShortClip[];
  jobId: string;
  onPreview: (clip: ShortClip) => void;
  onUpdateClip: (updated: ShortClip) => void;
}

export const ShortsReviewGrid: React.FC<ShortsReviewGridProps> = ({
  clips,
  jobId,
  onPreview,
  onUpdateClip,
}) => {
  if (!clips || clips.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-800 p-12 text-center bg-zinc-950/40">
        <Film className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-zinc-300">No Shorts Generated Yet</h3>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
          Submit a YouTube URL above to kick off the pipeline. AI-generated 9:16 Shorts with dynamic captions will appear here for review.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-white">
              Generated Shorts Review Panel
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold">
              {clips.length} {clips.length === 1 ? 'Short' : 'Shorts'} Ready
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Preview vertical 9:16 video formatting, edit titles, and publish directly to YouTube.
          </p>
        </div>
      </div>

      {/* Grid of Shorts Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clips.map((clip) => (
          <ShortCard
            key={clip.id}
            clip={clip}
            jobId={jobId}
            onPreview={onPreview}
            onUpdateClip={onUpdateClip}
          />
        ))}
      </div>
    </div>
  );
};
