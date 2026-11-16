from __future__ import annotations

import secrets
import time
from typing import Optional

# Sessoes em memoria: session_id -> {user_id, csrf, expires_at}
# Adequado para operacao local de maquina unica (escopo do projeto EducaFlow).
SESSIONS: dict[str, dict] = {}

SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 dias


def gerar_token() -> str:
    return secrets.token_urlsafe(32)


def nova_sessao(user_id: int) -> tuple[str, str]:
    session_id = gerar_token()
    csrf = gerar_token()
    SESSIONS[session_id] = {
        "user_id": user_id,
        "csrf": csrf,
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return session_id, csrf


def obter_sessao(session_id: Optional[str]) -> Optional[dict]:
    if not session_id:
        return None
    sessao = SESSIONS.get(session_id)
    if not sessao:
        return None
    if sessao["expires_at"] < time.time():
        SESSIONS.pop(session_id, None)
        return None
    return sessao


def remover_sessao(session_id: Optional[str]) -> None:
    if session_id:
        SESSIONS.pop(session_id, None)


def remover_sessoes_usuario(user_id: int, preservar: Optional[str] = None) -> int:
    """Encerra as sessoes de um usuario, opcionalmente preservando uma delas."""
    encerradas = 0
    for session_id, sessao in list(SESSIONS.items()):
        if sessao["user_id"] == user_id and session_id != preservar:
            SESSIONS.pop(session_id, None)
            encerradas += 1
    return encerradas


def limpar_sessoes_expiradas() -> None:
    agora = time.time()
    expirados = [sid for sid, s in SESSIONS.items() if s["expires_at"] < agora]
    for sid in expirados:
        SESSIONS.pop(sid, None)
