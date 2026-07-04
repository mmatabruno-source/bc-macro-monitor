"""Orquestração do fluxo IPCA: checar -> notificar -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.ipca.cliente_composicao import buscar_composicao_ipca
from src.ipca.cliente_sgs import buscar_ultimas_divulgacoes
from src.ipca.leitura_impacto import gerar_leitura
from src.ipca.modelos import DivulgacaoIpca

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_ipca"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "ipca"

TEXTO_DIRECAO = {"acelerou": "acelerou", "desacelerou": "desacelerou", "estavel": "estável"}
TEXTO_POSICAO = {"acima": "acima da meta", "abaixo": "abaixo da meta", "em_linha": "em linha com a meta"}

LARGURA_NOME = 27


def _fmt(valor):
    return f"{valor:.2f}".replace(".", ",")


def _montar_tabela_grupos(grupos):
    linhas = [f"{'Grupo':<{LARGURA_NOME}}{'Var%':>7}{'Peso%':>7}"]
    for grupo in grupos:
        linhas.append(
            f"{grupo.nome:<{LARGURA_NOME}}{_fmt(grupo.variacao_mensal):>7}{_fmt(grupo.peso_mensal):>7}"
        )
    return "\n".join(linhas)


def _montar_mensagem(mes_anterior, atual, grupos):
    leitura = gerar_leitura(mes_anterior, atual)
    tabela = _montar_tabela_grupos(grupos)
    return (
        f"📈 IPCA — {atual.mes_referencia}\n"
        f"Variação mensal: {atual.variacao_mensal}%\n"
        f"Leitura: {TEXTO_DIRECAO[leitura.direcao_vs_mes_anterior]} em relação ao mês anterior, "
        f"{TEXTO_POSICAO[leitura.posicao_vs_meta]}\n\n"
        f"Composição por grupo:\n"
        f"```\n{tabela}\n```"
    )


def _gravar_historico(divulgacao, grupos):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.mes_referencia}.json"
    dados = asdict(divulgacao)
    dados["grupos"] = [asdict(grupo) for grupo in grupos]
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do fluxo IPCA. Retorna True se um novo mês foi
    processado e notificado, False caso contrário."""
    divulgacoes = buscar_ultimas_divulgacoes()
    atual = divulgacoes[-1]
    mes_anterior_api = divulgacoes[-2]

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    anterior_registrado = DivulgacaoIpca(**estado_anterior) if estado_anterior else None

    if anterior_registrado is not None and anterior_registrado.mes_referencia == atual.mes_referencia:
        logger.info("Mês %s já processado — nada a fazer", atual.mes_referencia)
        return False

    _mes_composicao, _variacao_geral, grupos = buscar_composicao_ipca()
    mensagem = _montar_mensagem(mes_anterior_api, atual, grupos)

    token = os.environ.get("IPCA_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("IPCA_TELEGRAM_CHAT_ID")

    try:
        enviar_mensagem(mensagem, token, chat_id)
    except Exception as exc:
        logger.error("Falha ao enviar notificação do fluxo IPCA: %s", _sanitizar(str(exc), token))
        raise

    gravar_estado(CHAVE_ESTADO, asdict(atual), caminho=ESTADO_PATH)
    _gravar_historico(atual, grupos)

    return True
