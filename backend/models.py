# Pydantic models (request/response)

from pydantic import BaseModel

class PlaylistRequest(BaseModel):
    url: str
    max_videos: int = 10
    language: str = "pt"

class VideoSummary(BaseModel):
    video_id: str
    title: str
    duration_seconds: int
    key_topics: list[str]
    summary: str
    has_transcript: bool

class PlaylistSummary(BaseModel):
    playlist_title: str
    total_videos: int
    processed_videos: int
    videos: list[VideoSummary]
    overall_summary: str     # resumo geral da playlist inteira
    main_themes: list[str]