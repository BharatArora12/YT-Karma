from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionWord(BaseModel):
    word: str
    start: float
    end: float
    probability: float = 1.0


class TranscriptionSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: List[TranscriptionWord] = []


class TranscriptData(BaseModel):
    language: str = "en"
    duration: float = 0.0
    text: str = ""
    segments: List[TranscriptionSegment] = []


class ShortClipProposal(BaseModel):
    id: str
    start_time: float
    end_time: float
    duration: float
    title: str
    description: str
    tags: List[str] = []
    hook_reason: str = ""
    viral_score: int = Field(default=85, ge=1, le=100)
    rendered_filename: Optional[str] = None
    rendered_video_url: Optional[str] = None
    subtitle_filename: Optional[str] = None
    published_youtube_id: Optional[str] = None
    published_url: Optional[str] = None
    status: str = "pending"  # pending, rendering, ready, published, failed


class JobCreateRequest(BaseModel):
    youtube_url: str
    clip_count: int = Field(default=3, ge=1, le=5)
    min_duration: int = Field(default=30, ge=15, le=90)
    max_duration: int = Field(default=60, ge=20, le=120)


class JobResponse(BaseModel):
    job_id: str
    youtube_url: str
    video_title: Optional[str] = None
    video_author: Optional[str] = None
    video_thumbnail: Optional[str] = None
    original_duration: Optional[float] = None
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    current_step: str = "Initializing pipeline"
    error_message: Optional[str] = None
    clips: List[ShortClipProposal] = []
    created_at: str
    updated_at: str


class PublishRequest(BaseModel):
    job_id: str
    clip_id: str
    title: str
    description: str
    tags: List[str] = []
    privacy_status: str = Field(default="private", pattern="^(public|private|unlisted)$")


class PublishResponse(BaseModel):
    success: bool
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    message: str


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str


class GoogleAuthStatusResponse(BaseModel):
    authenticated: bool
    channel_title: Optional[str] = None
    channel_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    message: Optional[str] = None
