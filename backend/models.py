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

# Model do request (front para o back)
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

# Model do vídeo
class VideoSummary(BaseModel):
    """Resumo de um único vídeo da playlist."""
 
    video_id: str = Field(
        description="ID único do vídeo no YouTube (ex: dQw4w9WgXcQ)."
    )
    title: str = Field(
        description="Título do vídeo."
    )
    url: str = Field(
        description="URL direta do vídeo."
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        description="Duração do vídeo em segundos."
    )
    transcript_source: TranscriptSource = Field(
        description="Origem da transcrição usada para gerar o resumo."
    )
    key_topics: list[str] = Field(
        default_factory=list,
        description="Lista de tópicos principais abordados no vídeo."
    )
    summary: str = Field(
        description="Resumo detalhado do conteúdo do vídeo."
    )

# Model da playlist
class PlaylistSummary(BaseModel):
    """Resultado final retornado pelo agente e enviado ao frontend."""
 
    playlist_id: str = Field(
        description="ID único da playlist no YouTube."
    )
    playlist_title: str = Field(
        description="Título da playlist."
    )
    channel_name: str = Field(
        description="Nome do canal que publicou a playlist."
    )
    total_videos: int = Field(
        description="Total de vídeos na playlist (incluindo não processados)."
    )
    processed_videos: int = Field(
        description="Quantidade de vídeos efetivamente resumidos."
    )
    videos: list[VideoSummary] = Field(
        description="Lista de resumos individuais por vídeo."
    )
    main_themes: list[str] = Field(
        description="Temas recorrentes identificados em toda a playlist."
    )
    overall_summary: str = Field(
        description="Resumo geral cobrindo o conteúdo completo da playlist."
    )

# Erros
class ErrorResponse(BaseModel):
    """Formato padrão de erro retornado pela API."""
 
    error: str = Field(description="Mensagem de erro legível.")
    detail: Optional[str] = Field(default=None, description="Detalhes técnicos opcionais.")