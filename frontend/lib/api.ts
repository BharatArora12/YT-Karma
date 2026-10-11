import { JobData, HealthStatus } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function createJob(
  youtubeUrl: string,
  clipCount: number = 3,
  minDuration: number = 30,
  maxDuration: number = 60
): Promise<JobData> {
  const res = await fetch(`${API_BASE}/api/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
      clip_count: clipCount,
      min_duration: minDuration,
      max_duration: maxDuration,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create job (${res.status})`);
  }

  return res.json();
}

export async function getJob(jobId: string): Promise<JobData> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch job (${res.status})`);
  }
  return res.json();
}

export async function listJobs(): Promise<JobData[]> {
  const res = await fetch(`${API_BASE}/api/jobs`);
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function getHealth(): Promise<HealthStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getAuthUrl(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/auth/google/url`);
  if (!res.ok) throw new Error('Failed to get Google Auth URL');
  const data = await res.json();
  return data.auth_url;
}

export async function publishClip(params: {
  jobId: string;
  clipId: string;
  title: string;
  description: string;
  tags: string[];
  privacyStatus: 'public' | 'unlisted' | 'private';
}): Promise<{ success: boolean; youtube_video_id?: string; youtube_url?: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      job_id: params.jobId,
      clip_id: params.clipId,
      title: params.title,
      description: params.description,
      tags: params.tags,
      privacy_status: params.privacyStatus,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to publish clip.');
  }

  return res.json();
}

export function getMediaUrl(relativeUrl?: string | null): string {
  if (!relativeUrl) return '';
  if (relativeUrl.startsWith('http')) return relativeUrl;
  return `${API_BASE}${relativeUrl}`;
}

export async function retryJob(jobId: string): Promise<JobData> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/retry`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to retry job (${res.status})`);
  }
  return res.json();
}

