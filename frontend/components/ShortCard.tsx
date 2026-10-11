'use client';

import React, { useState } from 'react';
import { 
  Play, 
  Download, 
  FileText, 
  ExternalLink, 
  Sparkles, 
  Clock, 
  CheckCircle, 
  Edit3, 
  Loader2, 
  Share2, 
  Flame,
  Globe,
  Lock,
  EyeOff
} from 'lucide-react';
import { YouTubeIcon as Youtube } from './Icons';
import { ShortClip } from '../lib/types';
import { publishClip, getMediaUrl } from '../lib/api';

interface ShortCardProps {
  clip: ShortClip;
  jobId: string;
  onPreview: (clip: ShortClip) => void;
  onUpdateClip: (updated: ShortClip) => void;
}

export const ShortCard: React.FC<ShortCardProps> = ({
  clip,
  jobId,
  onPreview,
  onUpdateClip,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(clip.title);
  const [description, setDescription] = useState(clip.description);
  const [tagsStr, setTagsStr] = useState(clip.tags.join(', '));
  const [privacy, setPrivacy] = useState<'public' | 'unlisted' | 'private'>('private');
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishMessage, setPublishMessage] = useState<string | null>(null);

  const videoUrl = clip.rendered_filename ? getMediaUrl(clip.rendered_video_url) : '';
  const subtitleUrl = clip.subtitle_filename ? getMediaUrl(`/api/media/subtitles/${clip.subtitle_filename}`) : '';

  const handleSaveEdits = () => {
    const updatedTags = tagsStr.split(',').map((t) => t.trim()).filter(Boolean);
    const updated = {
      ...clip,
      title,
      description,
      tags: updatedTags,
    };
    onUpdateClip(updated);
    setIsEditing(false);
  };

  const handlePublish = async () => {
    try {
      setIsPublishing(true);
      setPublishMessage(null);
      const res = await publishClip({
        jobId,
        clipId: clip.id,
        title,
        description,
        tags: clip.tags,
        privacyStatus: privacy,
      });

      if (res.success) {
        onUpdateClip({
          ...clip,
          status: 'published',
          published_youtube_id: res.youtube_video_id,
          published_url: res.youtube_url,
        });
        setPublishMessage('Published successfully!');
      }
    } catch (e) {
      alert('Publishing error: ' + (e as Error).message);
    } finally {
      setIsPublishing(false);
    }
  };

  const isPublished = clip.status === 'published' || Boolean(clip.published_url);

  return (
    <div className="flex flex-col bg-zinc-900/90 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl hover:border-zinc-700/80 transition-all">
      {/* Top 9:16 Preview Card */}
      <div className="relative aspect-[9/16] bg-zinc-950 flex items-center justify-center overflow-hidden group">
        {videoUrl ? (
          <video
            src={videoUrl}
            controls={false}
            playsInline
            preload="metadata"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-center p-4">
            <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mx-auto mb-2 text-zinc-500">
              <Play className="w-5 h-5 ml-0.5" />
            </div>
            <p className="text-xs text-zinc-400">9:16 Vertical Render</p>
            <p className="text-[10px] text-zinc-400">{clip.status}</p>
          </div>
        )}

        {/* Hover Overlay with Big Play Button */}
        <div
          onClick={() => onPreview(clip)}
          className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center cursor-pointer p-4 text-center"
        >
          <div className="w-14 h-14 rounded-full bg-red-600/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform mb-2">
            <Play className="w-6 h-6 ml-1 fill-white" />
          </div>
          <span className="text-xs font-semibold text-white bg-black/60 px-3 py-1 rounded-full backdrop-blur-md">
            Click to Fullscreen Preview
          </span>
        </div>

        {/* Top Floating Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/75 backdrop-blur-md border border-white/10 text-white font-mono text-[11px]">
            <Clock className="w-3 h-3 text-zinc-400" />
            {clip.duration.toFixed(0)}s
          </span>

          <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-zinc-950 font-extrabold text-[11px] shadow-md">
            <Flame className="w-3 h-3 fill-zinc-950" />
            {clip.viral_score}/100 Hook
          </span>
        </div>

        {/* Bottom Timestamp indicator */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <span className="text-[10px] bg-black/80 px-2 py-0.5 rounded text-zinc-300 backdrop-blur-sm">
            {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s
          </span>
          {isPublished && (
            <span className="text-[10px] bg-emerald-500 text-black font-bold px-2 py-0.5 rounded flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Published
            </span>
          )}
        </div>
      </div>

      {/* Details & Metadata Panel */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-4">
        {/* Title & Edit Toggle */}
        <div>
          <div className="flex items-start justify-between gap-2 mb-1.5">
            {isEditing ? (
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full text-xs font-bold text-white bg-zinc-800 border border-zinc-700 rounded p-1.5 focus:outline-none focus:border-red-500"
              />
            ) : (
              <h3 className="text-sm font-bold text-zinc-100 line-clamp-2 leading-snug">
                {clip.title}
              </h3>
            )}
            <button
              onClick={() => (isEditing ? handleSaveEdits() : setIsEditing(true))}
              className="text-zinc-400 hover:text-white p-1 rounded hover:bg-zinc-800 shrink-0"
              title={isEditing ? 'Save edits' : 'Edit title & metadata'}
            >
              {isEditing ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <Edit3 className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* AI Hook Reason Callout */}
          <div className="p-2 rounded-lg bg-zinc-950/70 border border-zinc-800/80 text-[11px] text-zinc-400 space-y-1">
            <div className="flex items-center gap-1.5 text-zinc-300 font-medium">
              <Sparkles className="w-3 h-3 text-purple-400" />
              <span>Hook Analysis</span>
            </div>
            <p className="line-clamp-2 text-zinc-400 italic">
              &quot;{clip.hook_reason}&quot;
            </p>
          </div>

          {/* Description Editor / Viewer */}
          {isEditing && (
            <div className="mt-2 space-y-2">
              <textarea
                value={description}
                rows={2}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="YouTube Shorts Description..."
                className="w-full text-xs text-zinc-200 bg-zinc-800 border border-zinc-700 rounded p-1.5 focus:outline-none focus:border-red-500"
              />
              <input
                type="text"
                value={tagsStr}
                onChange={(e) => setTagsStr(e.target.value)}
                placeholder="Tags (comma separated)..."
                className="w-full text-xs text-zinc-200 bg-zinc-800 border border-zinc-700 rounded p-1.5 focus:outline-none focus:border-red-500"
              />
              <button
                onClick={handleSaveEdits}
                className="w-full py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white"
              >
                Save Changes
              </button>
            </div>
          )}

          {/* Tags preview */}
          {!isEditing && clip.tags && clip.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {clip.tags.slice(0, 4).map((tag, i) => (
                <span
                  key={i}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Publishing & Download Actions */}
        <div className="space-y-2 pt-2 border-t border-zinc-800">
          {/* Privacy Selector & Publish Button */}
          {isPublished ? (
            <a
              href={clip.published_url || `https://youtube.com/shorts/${clip.published_youtube_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition"
            >
              <Youtube className="w-4 h-4 text-red-500 fill-red-500" />
              <span>View on YouTube Shorts</span>
              <ExternalLink className="w-3.5 h-3.5 ml-1" />
            </a>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <select
                  value={privacy}
                  onChange={(e) => setPrivacy(e.target.value as any)}
                  className="bg-zinc-800 text-zinc-300 text-xs border border-zinc-700 rounded-lg px-2 py-1.5 focus:outline-none"
                >
                  <option value="private">🔒 Private</option>
                  <option value="unlisted">👁️ Unlisted</option>
                  <option value="public">🌐 Public</option>
                </select>

                <button
                  onClick={handlePublish}
                  disabled={isPublishing || !clip.rendered_filename}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-red-600 hover:bg-red-500 disabled:opacity-50 transition shadow-sm active:scale-95"
                >
                  {isPublishing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Publishing...</span>
                    </>
                  ) : (
                    <>
                      <Youtube className="w-3.5 h-3.5 fill-white" />
                      <span>Publish to YouTube</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Download Buttons */}
          <div className="flex items-center gap-2 pt-1">
            {videoUrl && (
              <a
                href={videoUrl}
                download={clip.rendered_filename || 'short.mp4'}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white text-[11px] font-medium transition"
              >
                <Download className="w-3 h-3" />
                <span>Save MP4</span>
              </a>
            )}

            {subtitleUrl && (
              <a
                href={subtitleUrl}
                download={clip.subtitle_filename || 'captions.ass'}
                className="flex items-center justify-center gap-1 py-1.5 px-2.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white text-[11px] font-medium transition"
                title="Download .ASS dynamic subtitle file"
              >
                <FileText className="w-3 h-3" />
                <span>.ASS</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
