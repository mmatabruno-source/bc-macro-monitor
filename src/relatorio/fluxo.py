"""Orquestração do fluxo Relatório de Política Monetária: checar -> notificar (aviso + análise) -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.relatorio.cliente_dataset import buscar_relatorio_mais_recente
from src.relatorio.gerador_analise import gerar_analise

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_relatorio"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "relatorios"


def _montar_aviso(atual):
    return (
        f"📄 *Relatório de Política Monetária ({atual.identificador})*\n\n"
        f"*Link*: {atual.link_pagina}"
    )


def _gravar_historico(relatorio, analise_gerada):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{relatorio.identificador}.json"
    dados = asdict(relatorio)
    dados["analise_gerada"] = analise_gerada
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do fluxo Relatório. Retorna True se um novo
    relatório foi processado e notificado (ao menos o aviso), False caso
    contrário."""
    atual = buscar_relatorio_mais_recente()

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    if estado_anterior is not None and estado_anterior.get("identificador") == atual.identificador:
        logger.info("Relatório %s já processado — nada a fazer", atual.identificador)
        return False

    token = os.environ.get("RELATORIO_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("RELATORIO_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(_montar_aviso(atual), token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar aviso de publicação: %s", _sanitizar(str(exc), token))
        raise

    analise_gerada = False
    try:
        analise = gerar_analise(atual.link_pdf)
        enviar_mensagem(f"🧭 *Visão crítica para o cidadão*\n{analise.visao_cidadao}", token, chat_id)
        enviar_mensagem(f"💼 *Visão do investidor*\n{analise.visao_investidor}", token, chat_id)
        analise_gerada = True
    except Exception as exc:
        # Fallback FR-006: falha na análise não impede que o relatório seja
        # considerado processado, já que o aviso de publicação foi enviado.
        mensagem_erro = _sanitizar(str(exc), token)
        mensagem_erro = _sanitizar(mensagem_erro, os.environ.get("ANTHROPIC_API_KEY"))
        logger.error("Falha ao gerar/enviar análise crítica (aviso já enviado): %s", mensagem_erro)

    gravar_estado(CHAVE_ESTADO, {"identificador": atual.identificador}, caminho=ESTADO_PATH)
    _gravar_historico(atual, analise_gerada)

    return True
