"""Isolamento de falha entre fluxos independentes na mesma execução."""

import logging

from src.comum.telegram import FalhaExternaTelegram, enviar_mensagem

logger = logging.getLogger(__name__)


def _executar_isolado(nome, verificar):
    try:
        processado = verificar()
        return {"processado": bool(processado), "falhou": False}
    except Exception as exc:  # isolamento deliberado — nunca deixa um fluxo derrubar outro
        logger.error("Erro inesperado ao processar %s: %s", nome, exc, exc_info=True)
        return {"processado": False, "falhou": True, "erro": exc}


def notificar_falha(contexto, erro, token, chat_id):
    """Avisa o bot dedicado ao fluxo sobre uma falha, sem travar a execução
    mesmo se o próprio Telegram for o componente falho."""
    mensagem = f"⚠️ Falha em {contexto}: {erro}\nTentando novamente na próxima execução."
    logger.error(mensagem)
    try:
        enviar_mensagem(mensagem, token=token, chat_id=chat_id)
    except FalhaExternaTelegram as exc:
        logger.error("Falha ao notificar via Telegram (sem retry adicional): %s", exc)
