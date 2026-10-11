'use client';

import React, { useEffect, useRef } from 'react';
import { X, Download, Flame, Sparkles, Clock } from 'lucide-react';
import { YouTubeIcon as Youtube } from './Icons';
import { ShortClip } from '../lib/types';
import { getMediaUrl } from '../lib/api';

interface VideoModalProps {
  clip: ShortClip | null;
  onClose: () => void;
}

export const VideoModal: React.FC<VideoModalProps> = ({ clip, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!clip) return null;

  const videoUrl = clip.rendered_filename ? getMediaUrl(clip.rendered_video_url) : '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Container */}
      <div className="relative w-full max-w-4xl bg-zinc-950 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row max-h-[90vh]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/70 hover:bg-black text-white/80 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Video Player (9:16 Aspect box) */}
        <div className="flex-1 bg-black flex items-center justify-center relative min-h-[420px] md:min-h-0">
          {videoUrl ? (
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              autoPlay
              playsInline
              className="max-h-[85vh] w-auto aspect-[9/16] object-contain"
            />
          ) : (
            <div className="text-zinc-500 text-sm">Rendering in progress...</div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="w-full md:w-80 p-6 flex flex-col justify-between overflow-y-auto border-t md:border-t-0 md:border-l border-zinc-800 bg-zinc-900/60">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 fill-amber-400" />
                {clip.viral_score}/100 Score
              </span>
              <span className="px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-300 text-xs flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {clip.duration.toFixed(0)}s
              </span>
            </div>

            <div>
              <h3 className="text-base font-bold text-white leading-snug">
                {clip.title}
              </h3>
              <p className="text-xs text-zinc-400 mt-2 line-clamp-4">
                {clip.description}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-zinc-950/80 border border-zinc-800 text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-zinc-300 font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>AI Hook Strategy</span>
              </div>
              <p className="text-zinc-400 text-[11px] leading-relaxed">
                {clip.hook_reason}
              </p>
            </div>

            {clip.tags && clip.tags.length > 0 && (
              <div>
                <label className="text-[11px] font-semibold text-zinc-400 block mb-1.5 uppercase tracking-wider">
                  Tags &amp; SEO
                </label>
                <div className="flex flex-wrap gap-1">
                  {clip.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-6 space-y-2">
            {videoUrl && (
              <a
                href={videoUrl}
                download={clip.rendered_filename || 'short.mp4'}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-semibold transition"
              >
                <Download className="w-4 h-4" />
                <span>Download Rendered MP4</span>
              </a>
            )}
            <button
              onClick={onClose}
              className="w-full py-2 text-zinc-400 hover:text-zinc-200 text-xs"
            >
              Close Preview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
