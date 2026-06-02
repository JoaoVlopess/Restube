 # YouTube API client
"""
services/youtube.py
 
Responsabilidade única: conversar com a YouTube Data API v3.
 
Este módulo não sabe nada sobre LLM, agentes ou resumos.
Ele só sabe buscar dados do YouTube e devolvê-los limpos e tipados.
O agente consome essas funções como tools sem precisar conhecer os detalhes.
"""
 
import os
import re
from dataclasses import dataclass
from typing import Optional
 
from googleapiclient.discovery import build
from dotenv import load_dotenv
 
load_dotenv()

@dataclass
class VideoMetadata:
    """Metadados de um único vídeo retornado pela API."""
    video_id: str
    title: str
    url: str
    duration_seconds: Optional[int]


@dataclass
class PlaylistMetadata:
    """Metadados gerais da playlist + lista de vídeos."""
    playlist_id: str
    title: str
    channel_name: str
    total_videos: int
    videos: list[VideoMetadata]


def _get_youtube_client():
    """
    Instancia o cliente da YouTube Data API v3.
 
    Separado em função para facilitar mock nos testes:
    você pode fazer patch só aqui sem mexer no resto do código.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError(
            "YOUTUBE_API_KEY não encontrada. "
            "Verifique se o arquivo .env está configurado."
        )
    return build("youtube", "v3", developerKey=api_key)


def extract_playlist_id(url: str) -> str:
    """
    Extrai o playlist_id de uma URL do YouTube.
 
    Aceita URL completa ou ID direto.
    Lança ValueError se não conseguir extrair.
    """
    # tenta extrair o parâmetro ?list= da URL
    match = re.search(r"[?&]list=([^&]+)", url)
    if match:
        return match.group(1)
 
    # se não achou na URL, verifica se o próprio input já é um ID
    # IDs de playlist começam com PL, FL, UU, RD, ou LL
    if re.match(r"^(PL|FL|UU|RD|LL)[a-zA-Z0-9_-]+$", url.strip()):
        return url.strip()
 
    raise ValueError(
        f"Não foi possível extrair o playlist_id de: {url}\n"
        "Esperado uma URL do tipo youtube.com/playlist?list=... "
        "ou um ID direto começando com PL."
    )

def _parse_duration(iso_duration: str) -> Optional[int]:
    """
    Converte duração ISO 8601 para segundos.
 
    Exemplos:
        PT4M13S → 253
        PT1H2M3S → 3723
        PT30S → 30
    """
    if not iso_duration:
        return None
 
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, iso_duration)
    if not match:
        return None
 
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
 
    return hours * 3600 + minutes * 60 + seconds

def _fetch_video_durations(youtube, video_ids: list[str]) -> dict[str, Optional[int]]:
    """
    Busca a duração de uma lista de vídeos.
 
    A API aceita até 50 IDs por chamada — já respeitamos isso
    porque buscamos no máximo 50 vídeos por página de playlist.
 
    Retorna um dict { video_id: duration_seconds }.
    """
    if not video_ids:
        return {}
 
    response = youtube.videos().list(
        part="contentDetails",
        id=",".join(video_ids),
        maxResults=50
    ).execute()
 
    return {
        item["id"]: _parse_duration(
            item["contentDetails"].get("duration", "")
        )
        for item in response.get("items", [])
    }


def fetch_playlist_metadata(url: str, max_videos: int = 10) -> PlaylistMetadata:
    """
    Busca todos os metadados de uma playlist do YouTube.
 
    Esta é a única função que o agente precisa conhecer.
    Toda a complexidade de paginação, autenticação e parsing fica aqui.
 
    Args:
        url: URL completa ou ID da playlist.
        max_videos: Limite de vídeos a retornar.
 
    Returns:
        PlaylistMetadata com título, canal e lista de vídeos.
 
    Raises:
        ValueError: Se a URL for inválida.
        HttpError: Se a API do YouTube retornar erro (cota, ID inválido, etc).
    """
    playlist_id = extract_playlist_id(url)
    youtube = _get_youtube_client()
 
    # --- Passo 1: busca metadados gerais da playlist ---
    playlist_response = youtube.playlists().list(
        part="snippet,contentDetails",
        id=playlist_id
    ).execute()
 
    items = playlist_response.get("items", [])
    if not items:
        raise ValueError(
            f"Playlist não encontrada: {playlist_id}\n"
            "Verifique se a playlist é pública e se o ID está correto."
        )
 
    playlist_info = items[0]
    playlist_title = playlist_info["snippet"]["title"]
    channel_name = playlist_info["snippet"]["channelTitle"]
    total_videos = playlist_info["contentDetails"]["itemCount"]
 
    # --- Passo 2: busca os vídeos da playlist (com paginação) ---
    # A API devolve no máximo 50 itens por página.
    # Usamos nextPageToken para continuar buscando até atingir max_videos.
    videos_raw = []
    next_page_token = None
 
    while len(videos_raw) < max_videos:
        # quantos ainda precisamos buscar nesta página
        remaining = max_videos - len(videos_raw)
        page_size = min(remaining, 50)  # máximo permitido pela API é 50
 
        page_response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=page_size,
            pageToken=next_page_token
        ).execute()
 
        videos_raw.extend(page_response.get("items", []))
 
        # se não há mais páginas, para
        next_page_token = page_response.get("nextPageToken")
        if not next_page_token:
            break
 
    # --- Passo 3: busca durações em chamada separada ---
    video_ids = [
        item["contentDetails"]["videoId"]
        for item in videos_raw
        # filtra vídeos privados/deletados que não têm ID
        if item["contentDetails"].get("videoId")
    ]
    durations = _fetch_video_durations(youtube, video_ids)
 
    # --- Passo 4: monta os objetos finais ---
    videos = []
    for item in videos_raw:
        video_id = item["contentDetails"].get("videoId")
 
        # ignora vídeos privados ou deletados
        if not video_id:
            continue
 
        # vídeos privados aparecem com título "[Private video]"
        title = item["snippet"].get("title", "")
        if title in ("[Private video]", "[Deleted video]"):
            continue
 
        videos.append(VideoMetadata(
            video_id=video_id,
            title=title,
            url=f"https://youtube.com/watch?v={video_id}",
            duration_seconds=durations.get(video_id),
        ))
 
    return PlaylistMetadata(
        playlist_id=playlist_id,
        title=playlist_title,
        channel_name=channel_name,
        total_videos=int(total_videos),
        videos=videos,
    )