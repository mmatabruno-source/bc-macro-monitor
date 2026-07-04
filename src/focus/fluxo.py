"""Orquestração do fluxo Focus/Copom: checar -> comparar -> notificar -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.focus.cliente_expectativas import buscar_proxima_reuniao
from src.focus.comparador import DivulgacaoFocus, comparar

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultima_expectativa_copom"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "focus"

TEXTO_DIRECAO = {
    "subiu": "subiu",
    "desceu": "desceu",
    "manteve": "manteve",
    "inicial": "valor inicial (sem divulgação anterior para comparar)",
}


def _montar_mensagem(anterior, atual, direcao):
    linhas = [
        f"📊 Focus — expectativa de Selic para {atual.reuniao_id}",
        f"Mediana: {atual.mediana_selic}",
        f"Direção: {TEXTO_DIRECAO[direcao]}",
    ]
    if anterior is not None and direcao != "inicial":
        linhas.append(f"Mediana anterior: {anterior.mediana_selic}")
    return "\n".join(linhas)


def _gravar_historico(divulgacao):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.data_referencia}.json"
    caminho.write_text(
        json.dumps(asdict(divulgacao), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do fluxo Focus. Retorna True se uma nova
    divulgação foi processada e notificada, False caso contrário."""
    atual = buscar_proxima_reuniao()

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    anterior = DivulgacaoFocus(**estado_anterior) if estado_anterior else None

    if (
        anterior is not None
        and anterior.reuniao_id == atual.reuniao_id
        and anterior.data_referencia == atual.data_referencia
    ):
        logger.info("Divulgação já processada (%s, %s) — nada a fazer", atual.reuniao_id, atual.data_referencia)
        return False

    direcao = comparar(anterior, atual)
    mensagem = _montar_mensagem(anterior, atual, direcao)

    token = os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FOCUS_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar notificação do fluxo Focus: %s", _sanitizar(str(exc), token))
        raise

    gravar_estado(CHAVE_ESTADO, asdict(atual), caminho=ESTADO_PATH)
    _gravar_historico(atual)

    return True
