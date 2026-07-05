"""Orquestração do Resumo Semanal do Focus: checar -> comparar -> montar mensagem -> notificar -> gravar estado."""

import json
import logging
import os
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.focus_resumo.cliente_expectativas_anuais import buscar_resumo_atual
from src.focus_resumo.comparador import comparar_valores

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_resumo_focus"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "focus_resumo"

TEXTO_DIRECAO = {"subiu": " (subiu)", "desceu": " (desceu)", "manteve": "", None: ""}

ORDEM_INDICADORES = ["IPCA", "Selic", "Câmbio", "PIB Total"]

CONFIG_INDICADOR = {
    "IPCA": {"emoji": "🛒", "titulo": "IPCA (a.a.)", "casas": 2, "sufixo": "%"},
    "Selic": {"emoji": "📊", "titulo": "Selic (a.a.)", "casas": 2, "sufixo": "%"},
    "Câmbio": {"emoji": "💲", "titulo": "Câmbio (R$/US$)", "casas": 3, "sufixo": ""},
    "PIB Total": {"emoji": "📦", "titulo": "PIB (var. % sobre o ano anterior)", "casas": 3, "sufixo": ""},
}


def _fmt(valor, casas):
    return f"{valor:.{casas}f}".replace(".", ",")


def _montar_mensagem(divulgacao, direcoes):
    linhas = [f"📋 *Resumo Focus — {divulgacao.data_referencia}*"]

    por_indicador = {}
    for item in divulgacao.valores:
        por_indicador.setdefault(item.indicador, []).append(item)

    for indicador in ORDEM_INDICADORES:
        itens = por_indicador.get(indicador)
        if not itens:
            continue
        config = CONFIG_INDICADOR[indicador]
        linhas.append(f"\n{config['emoji']} *{config['titulo']}*")
        for item in sorted(itens, key=lambda i: i.ano):
            chave = f"{item.indicador}:{item.ano}"
            direcao = direcoes.get(chave)
            valor_fmt = _fmt(item.valor, config["casas"])
            linhas.append(f"▪️ *{item.ano}*: {valor_fmt}{config['sufixo']}{TEXTO_DIRECAO[direcao]}")

    return "\n".join(linhas)


def _gravar_historico(divulgacao, valores_dict):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.data_referencia}.json"
    caminho.write_text(
        json.dumps(
            {"data_referencia": divulgacao.data_referencia, "valores": valores_dict},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do Resumo Semanal do Focus. Retorna True se
    uma nova divulgação foi processada e notificada, False caso contrário."""
    divulgacao = buscar_resumo_atual()

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    if estado_anterior is not None and estado_anterior.get("data_referencia") == divulgacao.data_referencia:
        logger.info("Divulgação %s já processada — nada a fazer", divulgacao.data_referencia)
        return False

    valores_anteriores = estado_anterior.get("valores", {}) if estado_anterior else {}
    direcoes = comparar_valores(valores_anteriores, divulgacao.valores)
    mensagem = _montar_mensagem(divulgacao, direcoes)

    token = os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FOCUS_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar resumo semanal do Focus: %s", _sanitizar(str(exc), token))
        raise

    novos_valores = {f"{item.indicador}:{item.ano}": item.valor for item in divulgacao.valores}
    gravar_estado(
        CHAVE_ESTADO,
        {"data_referencia": divulgacao.data_referencia, "valores": novos_valores},
        caminho=ESTADO_PATH,
    )
    _gravar_historico(divulgacao, novos_valores)

    return True
