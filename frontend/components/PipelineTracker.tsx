'use client';

import React from 'react';
import { 
  Download, 
  Mic, 
  Sparkles, 
  Scissors, 
  CheckCircle2, 
  Loader2, 
  Clock, 
  AlertCircle,
  Clock3,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { YouTubeIcon as Youtube } from './Icons';
import { JobData, JobStatus } from '../lib/types';

interface PipelineTrackerProps {
  job: JobData;
  onRetry?: (jobId: string) => void;
}

interface StepConfig {
  number: number;
  id: string;
  label: string;
  desc: string;
  icon: React.ElementType;
}

const STEPS: StepConfig[] = [
  {
    number: 1,
    id: 'downloading',
    label: 'Ingestion',
    desc: 'yt-dlp stream download & audio extraction',
    icon: Download,
  },
  {
    number: 2,
    id: 'transcribing',
    label: 'Transcription',
    desc: 'faster-whisper word-level timestamps',
    icon: Mic,
  },
  {
    number: 3,
    id: 'analyzing',
    label: 'AI Clip Selection',
    desc: 'Gemini 1.5 Flash hook & metadata analysis',
    icon: Sparkles,
  },
  {
    number: 4,
    id: 'rendering',
    label: 'Video Processing',
    desc: 'FFmpeg 9:16 vertical crop & .ass dynamic captions',
    icon: Scissors,
  },
  {
    number: 5,
    id: 'publishing',
    label: 'Publishing Ready',
    desc: 'YouTube Data API v3 integration',
    icon: Youtube,
  },
];

function getStepState(
  stepIdx: number,
  jobStatus: JobStatus,
  progress: number
): 'done' | 'active' | 'pending' | 'failed' {
  if (jobStatus === 'failed') {
    // Determine which step failed
    if (stepIdx === 0 && progress <= 30) return 'failed';
    if (stepIdx === 1 && progress > 30 && progress <= 55) return 'failed';
    if (stepIdx === 2 && progress > 55 && progress <= 70) return 'failed';
    if (stepIdx === 3 && progress > 70 && progress <= 95) return 'failed';
    if (stepIdx === 4 && progress > 95) return 'failed';
  }

  if (jobStatus === 'completed') return 'done';

  const thresholds = [30, 55, 70, 95, 100];
  const prevThreshold = stepIdx === 0 ? 0 : thresholds[stepIdx - 1];
  const currThreshold = thresholds[stepIdx];

  if (progress >= currThreshold) return 'done';
  if (progress > prevThreshold && progress < currThreshold) return 'active';
  return 'pending';
}

export const PipelineTracker: React.FC<PipelineTrackerProps> = ({ job, onRetry }) => {
  const isFailed = job.status === 'failed';
  const isDone = job.status === 'completed';

  return (
    <div className="mb-10 rounded-2xl bg-zinc-900/90 border border-zinc-800 p-6 shadow-xl relative overflow-hidden">
      {/* Top Video Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-zinc-800/80">
        <div className="flex items-center gap-4 min-w-0">
          {job.video_thumbnail ? (
            <img
              src={job.video_thumbnail}
              alt={job.video_title || 'Thumbnail'}
              className="w-20 h-12 rounded-lg object-cover ring-1 ring-zinc-700 shrink-0"
            />
          ) : (
            <div className="w-20 h-12 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-500 text-xs shrink-0">
              <Youtube className="w-6 h-6 text-zinc-600" />
            </div>
          )}

          <div className="min-w-0">
            <h2 className="text-base font-bold text-white truncate max-w-xl">
              {job.video_title || 'Processing YouTube Video...'}
            </h2>
            <div className="flex items-center gap-3 text-xs text-zinc-400 mt-0.5">
              <span>{job.video_author || 'Creator Unknown'}</span>
              {job.original_duration && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock3 className="w-3 h-3 text-zinc-400" />
                    {Math.floor(job.original_duration / 60)}m {Math.floor(job.original_duration % 60)}s
                  </span>
                </>
              )}
              <span>•</span>
              <span className="font-mono text-zinc-400">{job.job_id}</span>
            </div>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
          <div
            className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 ${
              isDone
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : isFailed
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
            }`}
          >
            {isDone ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            ) : isFailed ? (
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            ) : (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />
            )}
            <span className="capitalize">{job.status} ({job.progress}%)</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="my-6">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="font-medium text-zinc-300 flex items-center gap-2">
            {!isDone && !isFailed && <Loader2 className="w-3.5 h-3.5 animate-spin text-red-500" />}
            {job.current_step}
          </span>
          <span className="font-mono font-bold text-zinc-400">{job.progress}%</span>
        </div>

        <div className="w-full h-2.5 bg-zinc-800 rounded-full overflow-hidden p-0.5">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isFailed
                ? 'bg-rose-500'
                : isDone
                ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                : 'bg-gradient-to-r from-red-600 via-rose-500 to-amber-500'
            }`}
            style={{ width: `${Math.max(4, Math.min(100, job.progress))}%` }}
          />
        </div>
      </div>

      {/* 5-Step Milestones Stepper */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
        {STEPS.map((step, idx) => {
          const state = getStepState(idx, job.status, job.progress);
          const Icon = step.icon;

          return (
            <div
              key={step.number}
              className={`p-3.5 rounded-xl border transition-all ${
                state === 'done'
                  ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                  : state === 'active'
                  ? 'bg-zinc-800/90 border-red-500/60 shadow-lg shadow-red-500/10 ring-1 ring-red-500/30'
                  : state === 'failed'
                  ? 'bg-rose-950/20 border-rose-500/40 text-rose-200'
                  : 'bg-zinc-950/40 border-zinc-800/60 text-zinc-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                    state === 'done'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : state === 'active'
                      ? 'bg-red-500/20 text-red-400'
                      : state === 'failed'
                      ? 'bg-rose-500/20 text-rose-400'
                      : 'bg-zinc-800 text-zinc-500'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                <div>
                  {state === 'done' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {state === 'active' && <Loader2 className="w-4 h-4 animate-spin text-red-400" />}
                  {state === 'failed' && <AlertCircle className="w-4 h-4 text-rose-400" />}
                  {state === 'pending' && <Clock className="w-3.5 h-3.5 text-zinc-600" />}
                </div>
              </div>

              <div className="text-xs font-semibold text-zinc-200">
                Step {step.number}: {step.label}
              </div>
              <p className="text-[11px] text-zinc-400 mt-0.5 line-clamp-2">
                {step.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Error Callout if Failed */}
      {isFailed && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>Pipeline Execution Failed</span>
            </div>
            {onRetry && (
              <button
                onClick={() => onRetry(job.job_id)}
                className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs flex items-center gap-1.5 transition shadow-sm"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Pipeline</span>
              </button>
            )}
          </div>
          {job.error_message && (
            <p className="font-mono text-[11px] text-rose-400/90 pl-6 break-words">
              {job.error_message}
            </p>
          )}
        </div>
      )}
    </div>
  );
};
