from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TTSProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    GOOGLE = "google"
    AMAZON = "amazon"


class VideoFormat(str, Enum):
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True)
    email: str = Field(max_length=255, unique=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # API credentials (encrypted in production)
    reddit_client_id: Optional[str] = Field(default=None, max_length=500)
    reddit_client_secret: Optional[str] = Field(default=None, max_length=500)
    tts_api_key: Optional[str] = Field(default=None, max_length=500)

    # Relationships
    reddit_posts: List["RedditPost"] = Relationship(back_populates="user")
    background_videos: List["BackgroundVideo"] = Relationship(back_populates="user")
    video_jobs: List["VideoGenerationJob"] = Relationship(back_populates="user")
    tts_configs: List["TTSConfiguration"] = Relationship(back_populates="user")
    subtitle_styles: List["SubtitleStyle"] = Relationship(back_populates="user")


class RedditPost(SQLModel, table=True):
    __tablename__ = "reddit_posts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    reddit_id: str = Field(max_length=50, unique=True, index=True)
    subreddit: str = Field(max_length=100, index=True)
    title: str = Field(max_length=500)
    content: str = Field(default="")
    author: str = Field(max_length=100)
    score: int = Field(default=0)
    num_comments: int = Field(default=0)
    created_utc: datetime
    url: str = Field(max_length=500)
    permalink: str = Field(max_length=500)

    # Metadata
    word_count: int = Field(default=0)
    estimated_duration: Decimal = Field(default=Decimal("0"), decimal_places=2)  # in seconds

    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="reddit_posts")
    video_jobs: List["VideoGenerationJob"] = Relationship(back_populates="reddit_post")


class BackgroundVideo(SQLModel, table=True):
    __tablename__ = "background_videos"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int  # in bytes
    duration: Decimal = Field(decimal_places=2)  # in seconds
    width: int
    height: int
    fps: Decimal = Field(decimal_places=2)
    format: VideoFormat = Field(default=VideoFormat.MP4)

    # Metadata
    description: str = Field(default="", max_length=500)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))

    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="background_videos")
    video_jobs: List["VideoGenerationJob"] = Relationship(back_populates="background_video")


class TTSConfiguration(SQLModel, table=True):
    __tablename__ = "tts_configurations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    provider: TTSProvider = Field(default=TTSProvider.OPENAI)
    voice_id: str = Field(max_length=100)
    voice_name: str = Field(max_length=100)

    # Voice settings
    speed: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=3.0)
    pitch: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=2.0)
    volume: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=2.0)

    # Additional settings per provider
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    is_default: bool = Field(default=False)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="tts_configs")
    video_jobs: List["VideoGenerationJob"] = Relationship(back_populates="tts_config")


class SubtitleStyle(SQLModel, table=True):
    __tablename__ = "subtitle_styles"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)

    # Font settings
    font_family: str = Field(default="Arial", max_length=100)
    font_size: int = Field(default=24, ge=10, le=72)
    font_weight: str = Field(default="bold", max_length=20)
    font_color: str = Field(default="#FFFFFF", max_length=7)  # hex color

    # Background/outline settings
    background_color: Optional[str] = Field(default=None, max_length=7)  # hex color
    background_opacity: Decimal = Field(default=Decimal("0.8"), decimal_places=2, ge=0.0, le=1.0)
    outline_color: str = Field(default="#000000", max_length=7)  # hex color
    outline_width: int = Field(default=2, ge=0, le=10)

    # Position settings
    position_x: Decimal = Field(default=Decimal("0.5"), decimal_places=3, ge=0.0, le=1.0)  # relative position
    position_y: Decimal = Field(default=Decimal("0.8"), decimal_places=3, ge=0.0, le=1.0)  # relative position
    alignment: str = Field(default="center", max_length=20)  # left, center, right

    # Animation settings
    fade_in_duration: Decimal = Field(default=Decimal("0.5"), decimal_places=2, ge=0.0)
    fade_out_duration: Decimal = Field(default=Decimal("0.5"), decimal_places=2, ge=0.0)

    # Additional style options
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    is_default: bool = Field(default=False)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="subtitle_styles")
    video_jobs: List["VideoGenerationJob"] = Relationship(back_populates="subtitle_style")


class VideoGenerationJob(SQLModel, table=True):
    __tablename__ = "video_generation_jobs"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    job_name: str = Field(max_length=200)
    status: JobStatus = Field(default=JobStatus.PENDING)

    # Processing settings
    target_duration: Decimal = Field(decimal_places=2, ge=1.0)  # in seconds
    output_width: int = Field(default=1080, ge=480, le=1920)
    output_height: int = Field(default=1920, ge=480, le=1920)
    output_fps: int = Field(default=30, ge=24, le=60)
    output_format: VideoFormat = Field(default=VideoFormat.MP4)

    # Processing progress
    progress_percentage: Decimal = Field(default=Decimal("0"), decimal_places=2, ge=0.0, le=100.0)
    current_step: str = Field(default="", max_length=200)
    estimated_completion: Optional[datetime] = Field(default=None)

    # Output file info
    output_filename: Optional[str] = Field(default=None, max_length=255)
    output_file_path: Optional[str] = Field(default=None, max_length=500)
    output_file_size: Optional[int] = Field(default=None)  # in bytes

    # Error handling
    error_message: Optional[str] = Field(default=None, max_length=1000)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)

    # Processing metadata
    processing_log: List[str] = Field(default=[], sa_column=Column(JSON))
    processing_settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")
    reddit_post_id: int = Field(foreign_key="reddit_posts.id")
    background_video_id: int = Field(foreign_key="background_videos.id")
    tts_config_id: int = Field(foreign_key="tts_configurations.id")
    subtitle_style_id: int = Field(foreign_key="subtitle_styles.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="video_jobs")
    reddit_post: RedditPost = Relationship(back_populates="video_jobs")
    background_video: BackgroundVideo = Relationship(back_populates="video_jobs")
    tts_config: TTSConfiguration = Relationship(back_populates="video_jobs")
    subtitle_style: SubtitleStyle = Relationship(back_populates="video_jobs")
    progress_updates: List["JobProgressUpdate"] = Relationship(back_populates="video_job")


class JobProgressUpdate(SQLModel, table=True):
    __tablename__ = "job_progress_updates"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    progress_percentage: Decimal = Field(decimal_places=2, ge=0.0, le=100.0)
    step_name: str = Field(max_length=200)
    step_description: str = Field(default="", max_length=500)

    # Additional data for real-time updates
    update_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    video_job_id: int = Field(foreign_key="video_generation_jobs.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    video_job: VideoGenerationJob = Relationship(back_populates="progress_updates")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=100)
    email: str = Field(max_length=255)
    reddit_client_id: Optional[str] = Field(default=None, max_length=500)
    reddit_client_secret: Optional[str] = Field(default=None, max_length=500)
    tts_api_key: Optional[str] = Field(default=None, max_length=500)


class UserUpdate(SQLModel, table=False):
    username: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)
    reddit_client_id: Optional[str] = Field(default=None, max_length=500)
    reddit_client_secret: Optional[str] = Field(default=None, max_length=500)
    tts_api_key: Optional[str] = Field(default=None, max_length=500)


class RedditPostCreate(SQLModel, table=False):
    reddit_id: str = Field(max_length=50)
    subreddit: str = Field(max_length=100)
    title: str = Field(max_length=500)
    content: str = Field(default="")
    author: str = Field(max_length=100)
    score: int = Field(default=0)
    num_comments: int = Field(default=0)
    created_utc: datetime
    url: str = Field(max_length=500)
    permalink: str = Field(max_length=500)
    word_count: int = Field(default=0)
    estimated_duration: Decimal = Field(default=Decimal("0"), decimal_places=2)
    user_id: int


class BackgroundVideoCreate(SQLModel, table=False):
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int
    duration: Decimal = Field(decimal_places=2)
    width: int
    height: int
    fps: Decimal = Field(decimal_places=2)
    format: VideoFormat = Field(default=VideoFormat.MP4)
    description: str = Field(default="", max_length=500)
    tags: List[str] = Field(default=[])
    user_id: int


class BackgroundVideoUpdate(SQLModel, table=False):
    description: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[List[str]] = Field(default=None)


class TTSConfigurationCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    provider: TTSProvider = Field(default=TTSProvider.OPENAI)
    voice_id: str = Field(max_length=100)
    voice_name: str = Field(max_length=100)
    speed: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=3.0)
    pitch: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=2.0)
    volume: Decimal = Field(default=Decimal("1.0"), decimal_places=2, ge=0.1, le=2.0)
    settings: Dict[str, Any] = Field(default={})
    is_default: bool = Field(default=False)
    user_id: int


class TTSConfigurationUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    voice_id: Optional[str] = Field(default=None, max_length=100)
    voice_name: Optional[str] = Field(default=None, max_length=100)
    speed: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.1, le=3.0)
    pitch: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.1, le=2.0)
    volume: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.1, le=2.0)
    settings: Optional[Dict[str, Any]] = Field(default=None)
    is_default: Optional[bool] = Field(default=None)


class SubtitleStyleCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    font_family: str = Field(default="Arial", max_length=100)
    font_size: int = Field(default=24, ge=10, le=72)
    font_weight: str = Field(default="bold", max_length=20)
    font_color: str = Field(default="#FFFFFF", max_length=7)
    background_color: Optional[str] = Field(default=None, max_length=7)
    background_opacity: Decimal = Field(default=Decimal("0.8"), decimal_places=2, ge=0.0, le=1.0)
    outline_color: str = Field(default="#000000", max_length=7)
    outline_width: int = Field(default=2, ge=0, le=10)
    position_x: Decimal = Field(default=Decimal("0.5"), decimal_places=3, ge=0.0, le=1.0)
    position_y: Decimal = Field(default=Decimal("0.8"), decimal_places=3, ge=0.0, le=1.0)
    alignment: str = Field(default="center", max_length=20)
    fade_in_duration: Decimal = Field(default=Decimal("0.5"), decimal_places=2, ge=0.0)
    fade_out_duration: Decimal = Field(default=Decimal("0.5"), decimal_places=2, ge=0.0)
    settings: Dict[str, Any] = Field(default={})
    is_default: bool = Field(default=False)
    user_id: int


class SubtitleStyleUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    font_family: Optional[str] = Field(default=None, max_length=100)
    font_size: Optional[int] = Field(default=None, ge=10, le=72)
    font_weight: Optional[str] = Field(default=None, max_length=20)
    font_color: Optional[str] = Field(default=None, max_length=7)
    background_color: Optional[str] = Field(default=None, max_length=7)
    background_opacity: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0, le=1.0)
    outline_color: Optional[str] = Field(default=None, max_length=7)
    outline_width: Optional[int] = Field(default=None, ge=0, le=10)
    position_x: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0.0, le=1.0)
    position_y: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0.0, le=1.0)
    alignment: Optional[str] = Field(default=None, max_length=20)
    fade_in_duration: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    fade_out_duration: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0)
    settings: Optional[Dict[str, Any]] = Field(default=None)
    is_default: Optional[bool] = Field(default=None)


class VideoGenerationJobCreate(SQLModel, table=False):
    job_name: str = Field(max_length=200)
    target_duration: Decimal = Field(decimal_places=2, ge=1.0)
    output_width: int = Field(default=1080, ge=480, le=1920)
    output_height: int = Field(default=1920, ge=480, le=1920)
    output_fps: int = Field(default=30, ge=24, le=60)
    output_format: VideoFormat = Field(default=VideoFormat.MP4)
    processing_settings: Dict[str, Any] = Field(default={})
    user_id: int
    reddit_post_id: int
    background_video_id: int
    tts_config_id: int
    subtitle_style_id: int


class VideoGenerationJobUpdate(SQLModel, table=False):
    job_name: Optional[str] = Field(default=None, max_length=200)
    status: Optional[JobStatus] = Field(default=None)
    progress_percentage: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0.0, le=100.0)
    current_step: Optional[str] = Field(default=None, max_length=200)
    estimated_completion: Optional[datetime] = Field(default=None)
    output_filename: Optional[str] = Field(default=None, max_length=255)
    output_file_path: Optional[str] = Field(default=None, max_length=500)
    output_file_size: Optional[int] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=1000)


class JobProgressUpdateCreate(SQLModel, table=False):
    progress_percentage: Decimal = Field(decimal_places=2, ge=0.0, le=100.0)
    step_name: str = Field(max_length=200)
    step_description: str = Field(default="", max_length=500)
    update_metadata: Dict[str, Any] = Field(default={})
    video_job_id: int
