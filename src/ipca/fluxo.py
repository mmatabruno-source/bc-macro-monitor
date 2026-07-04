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
from src.ipca.leitura_impacto import META_INFLACAO_CENTRO, calcular_variacao_anualizada
from src.ipca.modelos import DivulgacaoIpca

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_ipca"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "ipca"

LARGURA_NOME = 27


def _fmt(valor):
    return f"{valor:.2f}".replace(".", ",")


def _montar_tabela_grupos(grupos):
    linhas = [f"{'Grupo':<{LARGURA_NOME}}{'Var%':>7}{'Peso%':>7}"]
    for grupo in sorted(grupos, key=lambda g: g.peso_mensal, reverse=True):
        linhas.append(
            f"{grupo.nome:<{LARGURA_NOME}}{_fmt(grupo.variacao_mensal):>7}{_fmt(grupo.peso_mensal):>7}"
        )
    return "\n".join(linhas)


def _buscar_composicao_com_fallback(mes_referencia_esperado):
    """Busca a composição por grupo do IPCA. Nunca propaga exceção: a fonte
    (IBGE) já se mostrou instável em produção (ver
    specs/003-ipca-mensal/decisoes/composicao-ipca-por-grupo.md) e uma falha
    aqui não pode bloquear o alerta principal do IPCA, que vem de uma fonte
    totalmente confiável (BC/SGS)."""
    try:
        mes_composicao, _variacao_geral, grupos = buscar_composicao_ipca()
    except Exception as exc:
        logger.warning("Composição por grupo do IPCA indisponível — enviando sem a tabela: %s", exc)
        return None

    if mes_composicao != mes_referencia_esperado:
        logger.warning(
            "Composição por grupo (%s) não bate com o mês do IPCA geral (%s) — enviando sem a tabela",
            mes_composicao, mes_referencia_esperado,
        )
        return None

    return grupos


def _mes_ano_anterior_esperado(mes_referencia):
    ano, mes = mes_referencia.split("-")
    return f"{int(ano) - 1}-{mes}"


def _buscar_mes_ano_anterior(divulgacoes, atual):
    """Retorna a divulgação de 12 meses atrás (mesmo mês do ano anterior),
    ou None se a API não tiver retornado dados suficientes ou o mês não
    bater com o esperado (nunca bloqueia a mensagem principal por causa
    disso)."""
    if len(divulgacoes) < 13:
        return None

    candidato = divulgacoes[-13]
    if candidato.mes_referencia != _mes_ano_anterior_esperado(atual.mes_referencia):
        logger.warning(
            "Mês do ano anterior (%s) não bate com o esperado para %s — omitindo da mensagem",
            candidato.mes_referencia, atual.mes_referencia,
        )
        return None

    return candidato


def _montar_mensagem(mes_anterior, atual, mes_ano_anterior, grupos):
    variacao_anualizada = calcular_variacao_anualizada(atual.variacao_mensal)
    linhas = [
        f"📈 *IPCA — {atual.mes_referencia}*",
        f"*Variação mensal*: {_fmt(atual.variacao_mensal)}%",
        f"*Mês anterior*: {_fmt(mes_anterior.variacao_mensal)}%",
    ]
    if mes_ano_anterior is not None:
        linhas.append(f"*Mês do ano anterior*: {_fmt(mes_ano_anterior.variacao_mensal)}%")
    linhas += [
        "",
        f"*Variação anualizada*: {_fmt(variacao_anualizada)}% a.a.",
        f"*Meta de inflação*: {_fmt(META_INFLACAO_CENTRO)}% a.a.",
    ]
    if grupos is not None:
        tabela = _montar_tabela_grupos(grupos)
        linhas.append(f"\nComposição por grupo:\n```\n{tabela}\n```")
    return "\n".join(linhas)


def _gravar_historico(divulgacao, grupos):
    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    caminho = HISTORICO_DIR / f"{divulgacao.mes_referencia}.json"
    dados = asdict(divulgacao)
    if grupos is not None:
        dados["grupos"] = [asdict(grupo) for grupo in grupos]
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def processar():
    """Executa uma checagem do fluxo IPCA. Retorna True se um novo mês foi
    processado e notificado, False caso contrário."""
    divulgacoes = buscar_ultimas_divulgacoes(quantidade=13)
    atual = divulgacoes[-1]
    mes_anterior_api = divulgacoes[-2]
    mes_ano_anterior = _buscar_mes_ano_anterior(divulgacoes, atual)

    estado_anterior = ler_estado(CHAVE_ESTADO, caminho=ESTADO_PATH)
    anterior_registrado = DivulgacaoIpca(**estado_anterior) if estado_anterior else None

    if anterior_registrado is not None and anterior_registrado.mes_referencia == atual.mes_referencia:
        logger.info("Mês %s já processado — nada a fazer", atual.mes_referencia)
        return False

    grupos = _buscar_composicao_com_fallback(atual.mes_referencia)
    mensagem = _montar_mensagem(mes_anterior_api, atual, mes_ano_anterior, grupos)

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
