 # Extração de transcrições


import re
from dataclasses import dataclass
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from typing import List, Dict


@dataclass
class TranscriptInfo:
    """Informações básicas sobre a transcrição do vídeo para facilitar o tratamento posterior"""
    texto: str
    idioma: str
    gerada_por_ia: bool
    proximo_passo: str
    disponivel: bool 

ytt_api = YouTubeTranscriptApi()

def extract_transcript(video_id):
    try:
        transcript_list = ytt_api.list(video_id)
        transcript = transcript_list.find_transcript(['pt', "en"])

    except TranscriptsDisabled:
        # "Erro: As transcrições estão desativadas para este vídeo."
        return TranscriptInfo(
            texto="",
            idioma="",
            gerada_por_ia=False,
            proximo_passo="sem_transcricao",
            disponivel=False
        )
    
    except NoTranscriptFound:
        # "Erro: O vídeo possui transcrições, mas nenhuma nos idiomas 'pt' ou 'en'."
        return TranscriptInfo(
            texto="",
            idioma="",
            gerada_por_ia=False,
            proximo_passo="sem_transcricao",
            disponivel=False
        )
    
    except Exception as e:
    # Captura outros erros (ex: ID inválido, vídeo privado ou bloqueio de IP)
        # "Erro: Ocorreu um erro inesperado."
        return TranscriptInfo(
            texto="",
            idioma="",
            gerada_por_ia=False,
            proximo_passo="sem_transcricao",
            disponivel=False
        )

    texto_final = transcript.fetch()
    texto_montado = _montar_texto(texto_final)

    # Transcrição manual em portugues: pronta para uso
    if transcript.language_code == 'pt' and not transcript.is_generated:
        status_tratamento = "pronto"
    # Transcrição gerada por IA em português: precisa de revisão de pontuação e formatação
    elif transcript.language_code == 'pt':
        status_tratamento = "revisar_pontuacao"
    # Transcrição manual em inglês: precisa de tradução de alta qualidade
    elif transcript.language_code == 'en' and not transcript.is_generated:
        status_tratamento = "requer_traducao_alta_qualidade"
    # Transcrição gerada por IA em inglês: precisa de tradução e revisão
    else:
        status_tratamento = "requer_traducao_e_revisao"


    return TranscriptInfo(
        texto=texto_montado,
        idioma=transcript.language_code,
        gerada_por_ia=transcript.is_generated,
        proximo_passo=status_tratamento,
        disponivel=True
    )


def _montar_texto(fragmentos: List[Dict], max_chars: int = 12000) -> str:
    partes = []

    for fragmento in fragmentos:
        texto = fragmento["text"]

        # remove ruídos comuns de transcrições automáticas
        texto = re.sub(r'\[.*?\]', '', texto)   # [Música], [Aplausos], etc
        texto = re.sub(r'>+\s*', '', texto)      # >> NARRADOR:
        texto = re.sub(r'♪.*?♪', '', texto)      # ♪ trilha ♪
        texto = texto.strip()

        if texto:  # ignora fragmentos que ficaram vazios após limpeza
            partes.append(texto)

    texto_completo = " ".join(partes)

    # normaliza espaços múltiplos que podem ter sobrado
    texto_completo = re.sub(r' +', ' ', texto_completo).strip()

    # trunca se necessário
    if len(texto_completo) > max_chars:
        texto_completo = texto_completo[:max_chars]

    return texto_completo