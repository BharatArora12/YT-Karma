'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from '../components/Navbar';
import { SystemHealthBanner } from '../components/SystemHealthBanner';
import { UrlInputSection } from '../components/UrlInputSection';
import { PipelineTracker } from '../components/PipelineTracker';
import { ShortsReviewGrid } from '../components/ShortsReviewGrid';
import { VideoModal } from '../components/VideoModal';
import { JobData, ShortClip, HealthStatus } from '../lib/types';
import { createJob, getJob, listJobs, getHealth, retryJob } from '../lib/api';
import { History, Sparkles, CheckCircle2, ChevronRight, Play } from 'lucide-react';
import { YouTubeIcon as Youtube } from '../components/Icons';

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [activeJob, setActiveJob] = useState<JobData | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPreviewClip, setSelectedPreviewClip] = useState<ShortClip | null>(null);
  const [authBannerNotice, setAuthBannerNotice] = useState<string | null>(null);

  // Fetch health and recent jobs
  const fetchHealthAndJobs = useCallback(async () => {
    try {
      const h = await getHealth();
      setHealth(h);
      const jobs = await listJobs();
      setRecentJobs(jobs);
      if (jobs.length > 0 && !activeJob) {
        setActiveJob(jobs[0]);
      }
    } catch {
      // Backend not yet reachable
    }
  }, [activeJob]);

  useEffect(() => {
    fetchHealthAndJobs();
    const interval = setInterval(fetchHealthAndJobs, 10000);
    return () => clearInterval(interval);
  }, [fetchHealthAndJobs]);

  // Check URL params for OAuth callbacks
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('auth') === 'success') {
        setAuthBannerNotice('YouTube Channel connected successfully!');
        window.history.replaceState({}, document.title, window.location.pathname);
        fetchHealthAndJobs();
      } else if (params.get('auth') === 'error') {
        setAuthBannerNotice('Authentication error: ' + (params.get('msg') || 'Failed'));
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, [fetchHealthAndJobs]);

  // Active Job Polling
  useEffect(() => {
    if (!activeJob) return;

    const isRunning =
      activeJob.status !== 'completed' &&
      activeJob.status !== 'failed' &&
      activeJob.status !== 'idle';

    if (!isRunning) return;

    const pollInterval = setInterval(async () => {
      try {
        const updated = await getJob(activeJob.job_id);
        setActiveJob(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          setIsLoading(false);
          // Refresh recent list
          listJobs().then(setRecentJobs);
        }
      } catch (err) {
        console.error('Error polling job:', err);
      }
    }, 1500);

    return () => clearInterval(pollInterval);
  }, [activeJob]);

  const handleStartPipeline = async (
    url: string,
    clipCount: number,
    minDur: number,
    maxDur: number
  ) => {
    try {
      setIsLoading(true);
      const newJob = await createJob(url, clipCount, minDur, maxDur);
      setActiveJob(newJob);
      setRecentJobs((prev) => [newJob, ...prev]);
    } catch (err) {
      alert('Failed to start pipeline: ' + (err as Error).message);
      setIsLoading(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      setIsLoading(true);
      const retried = await retryJob(jobId);
      setActiveJob(retried);
    } catch (err) {
      alert('Failed to retry pipeline: ' + (err as Error).message);
      setIsLoading(false);
    }
  };

  const handleUpdateClip = (updated: ShortClip) => {
    if (!activeJob) return;
    const updatedClips = activeJob.clips.map((c) => (c.id === updated.id ? updated : c));
    setActiveJob({
      ...activeJob,
      clips: updatedClips,
    });
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar health={health} onRefreshHealth={fetchHealthAndJobs} />

      {/* Main Dashboard Canvas */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Auth callback success toast */}
        {authBannerNotice && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{authBannerNotice}</span>
            </div>
            <button
              onClick={() => setAuthBannerNotice(null)}
              className="text-emerald-400 hover:text-emerald-200"
            >
              ✕
            </button>
          </div>
        )}

        {/* System Diagnostics Banner */}
        <SystemHealthBanner health={health} />

        {/* URL Input & Configuration Section */}
        <UrlInputSection onSubmit={handleStartPipeline} isLoading={isLoading} />

        {/* Active Pipeline Status Tracker */}
        {activeJob && <PipelineTracker job={activeJob} onRetry={handleRetryJob} />}

        {/* Review Panel for Generated Shorts */}
        {activeJob && (
          <ShortsReviewGrid
            clips={activeJob.clips}
            jobId={activeJob.job_id}
            onPreview={setSelectedPreviewClip}
            onUpdateClip={handleUpdateClip}
          />
        )}

        {/* Recent Jobs Drawer if multiple exist */}
        {recentJobs.length > 1 && (
          <div className="mt-16 pt-8 border-t border-zinc-800/80">
            <div className="flex items-center gap-2 mb-4 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              <History className="w-4 h-4" />
              <span>Previous Repurposing Sessions</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {recentJobs.map((j) => (
                <div
                  key={j.job_id}
                  onClick={() => setActiveJob(j)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between ${
                    activeJob?.job_id === j.job_id
                      ? 'bg-zinc-800/90 border-red-500/60 ring-1 ring-red-500/30'
                      : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700'
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="font-semibold text-zinc-200 truncate">
                      {j.video_title || j.youtube_url}
                    </div>
                    <div className="text-[10px] text-zinc-400 mt-0.5">
                      {j.clips?.length || 0} clips • {j.status}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-zinc-400 shrink-0" />
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Video Fullscreen Preview Modal */}
      <VideoModal
        clip={selectedPreviewClip}
        onClose={() => setSelectedPreviewClip(null)}
      />

      {/* Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950 py-6 mt-16 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-zinc-400">YT Shorts Management System</span>
            <span>•</span>
            <span>Next.js App Router &amp; FastAPI</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-zinc-400">
            <span>yt-dlp</span>
            <span>faster-whisper</span>
            <span>Gemini 1.5 Flash</span>
            <span>FFmpeg</span>
            <span>YouTube Data API v3</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
