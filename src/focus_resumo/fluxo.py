"""Orquestração do Resumo Semanal do Focus: checar -> comparar -> montar mensagem -> notificar -> gravar estado."""

import json
import logging
import os
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.focus_resumo.cliente_expectativas_anuais import buscar_datas_recentes, buscar_divulgacao
from src.focus_resumo.comparador import comparar_valores

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_resumo_focus"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "focus_resumo"

ORDEM_INDICADORES = ["IPCA", "Selic", "Câmbio", "PIB Total"]

CONFIG_INDICADOR = {
    "IPCA": {"emoji": "🛒", "titulo": "IPCA (a.a.)", "casas": 2, "sufixo": "%"},
    "Selic": {"emoji": "📊", "titulo": "Selic (a.a.)", "casas": 2, "sufixo": "%"},
    "Câmbio": {"emoji": "💲", "titulo": "Câmbio (BRL/USD)", "casas": 3, "sufixo": ""},
    "PIB Total": {"emoji": "📦", "titulo": "PIB (var. sobre o ano anterior)", "casas": 3, "sufixo": "%"},
}


def _fmt(valor, casas):
    return f"{valor:.{casas}f}".replace(".", ",")


def _texto_direcao(direcao, delta, casas):
    if direcao is None:
        return ""
    if direcao == "subiu":
        return f" (▲ {_fmt(delta, casas)} p.p.)"
    if direcao == "desceu":
        return f" (▼ {_fmt(abs(delta), casas)} p.p.)"
    return " (= 0 p.p.)"


def _montar_mensagem(divulgacao, direcoes, valores_anteriores):
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
            anterior = valores_anteriores.get(chave)
            delta = item.valor - anterior if anterior is not None else None
            valor_fmt = _fmt(item.valor, config["casas"])
            linhas.append(
                f"▪️ *{item.ano}*: {valor_fmt}{config['sufixo']}"
                f"{_texto_direcao(direcao, delta, config['casas'])}"
            )

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


def _buscar_penultima_com_fallback(datas):
    """Busca a divulgação penúltima (para a comparação semanal, FR-004).
    Nunca propaga exceção: a comparação é um enriquecimento da mensagem
    principal, não pode bloquear o envio do resumo (mesmo padrão de
    fallback já usado em outros fluxos, ex. composição do IPCA)."""
    if len(datas) < 2:
        return None
    try:
        return buscar_divulgacao(datas[1])
    except Exception as exc:
        logger.warning("Divulgação penúltima indisponível — enviando sem comparação: %s", exc)
        return None


def processar():
    """Executa uma checagem do Resumo Semanal do Focus. Retorna True se
    uma nova divulgação foi processada e notificada, False caso contrário.

    A comparação semanal (FR-004) sempre busca a divulgação mais recente E
    a penúltima diretamente da API — nunca depende de valores persistidos
    de uma execução anterior, que poderiam estar ausentes/desatualizados."""
    datas = buscar_datas_recentes()
    atual = buscar_divulgacao(datas[0])

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    if estado_anterior is not None and estado_anterior.get("data_referencia") == atual.data_referencia:
        logger.info("Divulgação %s já processada — nada a fazer", atual.data_referencia)
        return False

    penultima = _buscar_penultima_com_fallback(datas)
    valores_penultima = (
        {f"{item.indicador}:{item.ano}": item.valor for item in penultima.valores}
        if penultima is not None
        else {}
    )
    direcoes = comparar_valores(valores_penultima, atual.valores)
    mensagem = _montar_mensagem(atual, direcoes, valores_penultima)

    token = os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FOCUS_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar resumo semanal do Focus: %s", _sanitizar(str(exc), token))
        raise

    novos_valores = {f"{item.indicador}:{item.ano}": item.valor for item in atual.valores}
    gravar_estado(
        CHAVE_ESTADO,
        {"data_referencia": atual.data_referencia, "valores": novos_valores},
        caminho=ESTADO_PATH,
    )
    _gravar_historico(atual, novos_valores)

    return True
