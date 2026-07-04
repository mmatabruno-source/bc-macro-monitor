"""Orquestração do fluxo Focus/Copom: checar -> comparar -> notificar -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.focus.calendario_copom import formatar_periodo_reuniao
from src.focus.cliente_expectativas import buscar_proxima_reuniao
from src.focus.cliente_selic_atual import buscar_selic_vigente
from src.focus.comparador import DivulgacaoFocus, calcular_variacao

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultima_expectativa_copom"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "focus"


def _fmt_pp(valor):
    sinal = "+" if valor > 0 else "-" if valor < 0 else ""
    texto = f"{sinal}{abs(valor):.2f}".replace(".", ",")
    return f"{texto} p.p."


def _fmt_pct(valor):
    return f"{valor:.2f}".replace(".", ",")


def _montar_mensagem(atual, selic_vigente):
    variacao, emoji = calcular_variacao(selic_vigente, atual.mediana_selic)
    periodo = formatar_periodo_reuniao(atual.reuniao_id)
    return "\n".join([
        f"📢 *Expectativas Copom - Focus {atual.data_referencia}*",
        "",
        f"{emoji} Projeta-se uma *variação de {_fmt_pp(variacao)}* na Selic",
        f"▪️ *Próxima reunião*: {periodo}",
        f"▪️ *Atual*: {_fmt_pct(selic_vigente)}% a.a.",
        f"▪️ *Projeção Focus*: {_fmt_pct(atual.mediana_selic)}% a.a. (mediana)",
    ])


def _gravar_historico(divulgacao, selic_vigente):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.data_referencia}.json"
    dados = asdict(divulgacao)
    dados["selic_vigente"] = selic_vigente
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
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

    selic_vigente = buscar_selic_vigente()
    mensagem = _montar_mensagem(atual, selic_vigente)

    token = os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FOCUS_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar notificação do fluxo Focus: %s", _sanitizar(str(exc), token))
        raise

    gravar_estado(CHAVE_ESTADO, asdict(atual), caminho=ESTADO_PATH)
    _gravar_historico(atual, selic_vigente)

    return True
