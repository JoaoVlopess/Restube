# Playlist Summarizer — Contexto do Projeto

## Stack
- Backend: Python 3.12, FastAPI, PydanticAI
- LLM: GROK via PydanticAI
- Frontend: HTML + CSS + Vanilla JS (sem frameworks)
- Deps principais: youtube-transcript-api, httpx

## Comandos
- Rodar backend: `uvicorn backend.main:app --reload`
- Rodar testes: `pytest backend/tests/`
- Instalar deps: `pip install -r requirements.txt`

## Arquitetura
- `backend/models.py` — todos os Pydantic models (nunca misture models com lógica)
- `backend/agent.py` — PydanticAI agent + tools
- `backend/services/` — clientes externos (YouTube API, transcrição)
- `frontend/` — HTML/CSS/JS estáticos, consumem a API via fetch()

## Regras
- Todo endpoint FastAPI deve ter tipagem completa com Pydantic
- Nunca commitar a .env ou API keys
- Funções de tools do agente devem ter docstring explicando o que fazem
- Tratar o caso de vídeo sem transcrição (has_transcript: false)

## O que NÃO fazer
- Não usar ORM (projeto simples, sem banco por enquanto)
- Não adicionar dependências sem discutir primeiro