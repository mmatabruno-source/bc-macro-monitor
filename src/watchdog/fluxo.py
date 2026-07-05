"""Orquestração do watchdog: consultar execuções de monitor.yml -> avaliar
-> alertar se necessário. Roda em workflow separado (watchdog.yml), nunca
dentro de monitor.yml — ver constituição, Architecture Constraints."""

import logging
import os

from src.comum.telegram import _sanitizar, enviar_mensagem
from src.watchdog.cliente_actions import buscar_execucoes_recentes
from src.watchdog.verificar import avaliar_execucoes

logger = logging.getLogger(__name__)

WORKFLOW_MONITORADO = "monitor.yml"


def processar():
    """Executa uma checagem do watchdog. Retorna True se um alerta foi
    enviado, False caso contrário (inclusive quando está tudo bem)."""
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/")
    github_token = os.environ["GITHUB_TOKEN"]

    execucoes = buscar_execucoes_recentes(owner, repo, WORKFLOW_MONITORADO, github_token)
    deve_alertar, motivo = avaliar_execucoes(execucoes)

    if not deve_alertar:
        logger.info("Watchdog: monitor.yml está saudável — nada a fazer")
        return False

    token = os.environ.get("WATCHDOG_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("WATCHDOG_TELEGRAM_CHAT_ID")
    mensagem = f"🚨 Watchdog: {motivo}"

    if not token or not chat_id:
        logger.error(
            "Watchdog detectou problema mas WATCHDOG_TELEGRAM_BOT_TOKEN/CHAT_ID "
            "não estão configurados — não foi possível alertar: %s",
            motivo,
        )
        return False

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar alerta do watchdog: %s", _sanitizar(str(exc), token))
        raise

    return True
