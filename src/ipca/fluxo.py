"""Orquestração do fluxo IPCA: checar -> notificar -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.ipca.cliente_sgs import buscar_ultimas_divulgacoes
from src.ipca.modelos import DivulgacaoIpca

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_ipca"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "ipca"


def _montar_mensagem(atual):
    return (
        f"📈 IPCA — {atual.mes_referencia}\n"
        f"Variação mensal: {atual.variacao_mensal}%"
    )


def _gravar_historico(divulgacao):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.mes_referencia}.json"
    caminho.write_text(
        json.dumps(asdict(divulgacao), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do fluxo IPCA. Retorna True se um novo mês foi
    processado e notificado, False caso contrário."""
    divulgacoes = buscar_ultimas_divulgacoes()
    atual = divulgacoes[-1]

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    anterior_registrado = DivulgacaoIpca(**estado_anterior) if estado_anterior else None

    if anterior_registrado is not None and anterior_registrado.mes_referencia == atual.mes_referencia:
        logger.info("Mês %s já processado — nada a fazer", atual.mes_referencia)
        return False

    mensagem = _montar_mensagem(atual)

    token = os.environ.get("IPCA_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("IPCA_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar notificação do fluxo IPCA: %s", _sanitizar(str(exc), token))
        raise

    gravar_estado(CHAVE_ESTADO, asdict(atual), caminho=ESTADO_PATH)
    _gravar_historico(atual)

    return True
