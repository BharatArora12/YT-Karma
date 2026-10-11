# YT Shorts Management System

An automated, end-to-end YouTube-to-Shorts repurposing and publishing platform. Powered by **Next.js 16 (App Router)** and **FastAPI (Python 3.11+)**.

---

## ⚡ Core Architecture

```
YT Shorts Management System/
├── backend/
│   ├── .venv/                         # Python virtual environment
│   ├── requirements.txt               # Backend dependencies
│   ├── .env.example                   # Environment configuration template
│   ├── storage/                       # Local media and artifact store
│   │   ├── downloads/                 # yt-dlp downloaded video & audio streams
│   │   ├── transcripts/               # faster-whisper word-level transcripts (JSON)
│   │   ├── subtitles/                 # Generated .ass dynamic caption files
│   │   ├── output_shorts/             # Rendered vertical 9:16 MP4 Shorts
│   │   └── tokens/                    # OAuth token sessions & credentials
│   └── app/
│       ├── main.py                    # FastAPI entrypoint, CORS, diagnostic endpoints
│       ├── config.py                  # Pydantic Settings & environment variables
│       ├── models/
│       │   └── schemas.py             # Pydantic schemas for jobs, clips & publishing
│       ├── services/
│       │   ├── pipeline_worker.py     # Sequential 5-step asynchronous pipeline coordinator
│       │   ├── ingestion.py           # Step 1: yt-dlp video/audio download
│       │   ├── transcription.py       # Step 2: faster-whisper word timestamp transcription
│       │   ├── ai_clip_selector.py    # Step 3: Google Gemini 1.5 Flash hook & metadata selection
│       │   ├── subtitle_generator.py  # High-impact .ass dynamic word highlight generator
│       │   ├── video_processor.py     # Step 4: FFmpeg 16:9 -> 9:16 crop & subtitle burner
│       │   └── youtube_publisher.py   # Step 5: Google OAuth 2.0 & YouTube Data API v3 upload
│       ├── api/
│       │   ├── routes_jobs.py         # Job trigger, progress polling, and transcripts
│       │   ├── routes_publish.py      # OAuth connect flow & YouTube publishing
│       │   └── routes_media.py        # Stream rendered shorts & subtitle files
│       └── utils/
│           └── ffmpeg_checker.py      # FFmpeg discovery and diagnostic helper
│
├── frontend/                          # Next.js App Router (TypeScript + Tailwind CSS)
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with Inter font & dark theme
│   │   ├── page.tsx                   # Interactive dashboard (URL input, Tracker, Review panel)
│   │   └── globals.css                # Tailwind CSS styling
│   ├── components/
│   │   ├── Navbar.tsx                 # Branding, backend status, YouTube OAuth connection
│   │   ├── SystemHealthBanner.tsx     # Toolchain health pills (FFmpeg, Gemini, Whisper)
│   │   ├── UrlInputSection.tsx        # YouTube URL input, samples, & duration controls
│   │   ├── PipelineTracker.tsx        # 5-step interactive milestone status tracker
│   │   ├── ShortsReviewGrid.tsx       # Grid container for generated Shorts
│   │   ├── ShortCard.tsx              # 9:16 preview, metadata editor, one-click publish
│   │   ├── VideoModal.tsx             # Fullscreen video preview with custom controls
│   │   └── Icons.tsx                  # Vector icons & branding
│   └── lib/
│       ├── api.ts                     # REST client for backend communication
│       └── types.ts                   # TypeScript interfaces
│
├── start_backend.bat                  # One-click backend startup script
├── start_frontend.bat                 # One-click frontend startup script
└── README.md
```

---

## 🚀 The 5-Step Automated Pipeline

1. **Ingestion Endpoint (`yt-dlp`)**: Accepts any public YouTube URL from the frontend and downloads the highest quality MP4 video and audio streams locally.
2. **Transcription Service (`faster-whisper`)**: Processes the extracted audio using `faster-whisper` on CPU or GPU with `word_timestamps=True` to create millisecond-accurate timestamps for every spoken word.
3. **AI Clip Selection & Metadata (`Google Gemini 1.5 Flash`)**: Transmits the timestamped transcript to Gemini 1.5 Flash. The model pinpoints 1–3 viral, standalone 30–60 second segments and generates high-CTR titles (with emojis), viral descriptions (with hashtags), search tags, and hook analyses.
4. **Video Processing (`FFmpeg`)**: Converts the horizontal 16:9 stream into a vertical 9:16 aspect ratio (1080x1920). Generates dynamic `.ass` subtitles with active-word highlighting (Alex Hormozi / MrBeast style) and burns captions directly onto the video.
5. **Publishing Integration (`YouTube Data API v3`)**: Features Google OAuth 2.0 authentication. Uploads the final rendered `.mp4` directly to the creator's YouTube channel with the AI-generated metadata in one click.

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **FFmpeg**:
  - Windows: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH (or configure `FFMPEG_PATH` in `backend/.env`).

### 2. Configure Backend Environment
Navigate to `backend/` and create `.env` from `.env.example`:
```bash
cd backend
copy .env.example .env
```
Open `backend/.env` and optionally configure:
- `GEMINI_API_KEY`: Your key from [Google AI Studio](https://aistudio.google.com/) (if empty, smart heuristic fallbacks are used).
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: From Google Cloud Console with YouTube Data API v3 enabled (or place `client_secrets.json` in `backend/`).
- `FFMPEG_PATH`: Path to `ffmpeg.exe` if not added to your system PATH.

### 3. Launch the Backend
```bash
# Windows shortcut:
.\start_backend.bat

# Or manual:
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation will be available at: `http://localhost:8000/docs`

### 4. Launch the Frontend
```bash
# Windows shortcut:
.\start_frontend.bat

# Or manual:
cd frontend
npm run dev
```
Open your browser to: `http://localhost:3000`

---

## 📡 API Endpoints

- `GET /api/health` - Subsystem diagnostics (FFmpeg, Gemini, Whisper, OAuth).
- `POST /api/jobs` - Trigger the 5-step automated pipeline.
- `GET /api/jobs` - List all recent jobs.
- `GET /api/jobs/{job_id}` - Real-time progress and generated clips.
- `GET /api/jobs/{job_id}/transcript` - Timestamped transcript.
- `GET /api/auth/google/url` - Generate Google OAuth URL.
- `GET /api/auth/google/callback` - OAuth redirect handler.
- `GET /api/auth/google/status` - Connected YouTube channel profile.
- `POST /api/publish` - Upload rendered Short directly to YouTube.
- `GET /api/media/shorts/{filename}` - Stream rendered vertical 9:16 MP4.
