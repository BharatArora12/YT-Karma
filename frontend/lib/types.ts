export type JobStatus =
  | 'idle'
  | 'queued'
  | 'downloading'
  | 'transcribing'
  | 'analyzing'
  | 'rendering'
  | 'completed'
  | 'failed';

export interface ShortClip {
  id: string;
  start_time: number;
  end_time: number;
  duration: number;
  title: string;
  description: string;
  tags: string[];
  hook_reason: string;
  viral_score: number;
  rendered_filename?: string | null;
  rendered_video_url?: string | null;
  subtitle_filename?: string | null;
  published_youtube_id?: string | null;
  published_url?: string | null;
  status: 'pending' | 'rendering' | 'ready' | 'published' | 'failed';
}

export interface JobData {
  job_id: string;
  youtube_url: string;
  video_title?: string | null;
  video_author?: string | null;
  video_thumbnail?: string | null;
  original_duration?: number | null;
  status: JobStatus;
  progress: number;
  current_step: string;
  error_message?: string | null;
  clips: ShortClip[];
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
  python_version: string;
  ffmpeg: {
    available: boolean;
    message: string;
  };
  gemini: {
    configured: boolean;
    model: string;
  };
  youtube_oauth: {
    authenticated: boolean;
    channel_title?: string | null;
    channel_id?: string | null;
  };
  whisper: {
    model_size: string;
    device: string;
    compute_type: string;
  };
}
