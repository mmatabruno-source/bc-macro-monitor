"""Lembrete anual (31/07) para coletar o calendário de reuniões do Copom
do ano seguinte e atualizar src/focus/calendario_copom.py — esse
calendário não vem de nenhuma API (não existe uma), é cadastrado
manualmente, e precisa de atualização anual quando o BC publica o
calendário do ano seguinte."""

import logging
import os
from datetime import datetime

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_lembrete_calendario_copom"
PRIMEIRO_ANO = 2027


def _montar_mensagem(ano_seguinte):
    return (
        f"🗓️ *Lembrete anual*\n\n"
        f"Colete o calendário oficial de reuniões do Copom para {ano_seguinte} "
        f"(BC costuma publicar no final de Junho) e cole no chat com "
        f"o Claude Code, para atualizar `src/focus/calendario_copom.py`."
    )


def processar():
    """Executa a checagem do lembrete anual. Retorna True se o lembrete
    foi enviado nesta execução, False caso contrário (ano ainda não
    chegou em 2027, ou lembrete deste ano já enviado)."""
    ano_atual = datetime.now().year

    if ano_atual < PRIMEIRO_ANO:
        logger.info("Lembrete de calendário do Copom começa em %d — nada a fazer ainda", PRIMEIRO_ANO)
        return False

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    if estado_anterior is not None and estado_anterior.get("ano") == ano_atual:
        logger.info("Lembrete de %d já enviado — nada a fazer", ano_atual)
        return False

    token = os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FOCUS_TELEGRAM_CHAT_ID")
    mensagem = _montar_mensagem(ano_atual + 1)

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar lembrete de calendário do Copom: %s", _sanitizar(str(exc), token))
        raise

    gravar_estado(CHAVE_ESTADO, {"ano": ano_atual}, caminho=ESTADO_PATH)

    return True
