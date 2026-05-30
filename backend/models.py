# Pydantic models (request/response)

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from enum import Enum
 
class SummaryLanguage(str, Enum):
    PORTUGUESE = "pt"
    ENGLISH = "en"
    SPANISH = "es"

class TranscriptSource(str, Enum):
    MANUAL = "manual"       # legenda enviada pelo criador do vídeo
    AUTO = "auto"           # legenda gerada automaticamente pelo YouTube
    NONE = "none"           # vídeo sem transcrição disponível

#request
class PlaylistRequest(BaseModel):
    """Body do POST /summarize enviado pelo frontend."""
 
    url: HttpUrl = Field(
        description="URL completa da playlist do YouTube."
    )
    max_videos: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Número máximo de vídeos a processar."
    )
    language: SummaryLanguage = Field(
        default=SummaryLanguage.PORTUGUESE,
        description="Idioma preferido para os resumos gerados."
    )

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