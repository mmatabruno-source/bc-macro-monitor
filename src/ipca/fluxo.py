"""Orquestração do fluxo IPCA: checar -> notificar -> gravar estado."""

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from src.comum.estado import ESTADO_PATH, gravar_estado, ler_estado
from src.comum.telegram import _sanitizar, enviar_mensagem
from src.ipca.cliente_composicao import NUMERO_GRUPO, buscar_composicao_ipca, buscar_itens_por_grupo
from src.ipca.cliente_sgs import buscar_ultimas_divulgacoes
from src.ipca.leitura_impacto import META_INFLACAO_CENTRO, calcular_variacao_anualizada
from src.ipca.modelos import DivulgacaoIpca

logger = logging.getLogger(__name__)

CHAVE_ESTADO = "ultimo_ipca"
HISTORICO_DIR = Path(__file__).resolve().parent.parent.parent / "historico" / "ipca"

LARGURA_NOME = 27


def _fmt(valor):
    return f"{valor:.2f}".replace(".", ",")


def _contribuicao(grupo):
    return grupo.variacao_mensal * grupo.peso_mensal


def _montar_tabela_grupos(grupos):
    linhas = [f"{'Grupo':<{LARGURA_NOME}}{'Var%':>7}{'Peso%':>7}{'Contrib':>9}"]
    for grupo in sorted(grupos, key=_contribuicao, reverse=True):
        linhas.append(
            f"{grupo.nome:<{LARGURA_NOME}}{_fmt(grupo.variacao_mensal):>7}"
            f"{_fmt(grupo.peso_mensal):>7}{_fmt(_contribuicao(grupo)):>9}"
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


def _top3_grupos_que_mais_subiram(grupos):
    candidatos = [g for g in grupos if g.variacao_mensal > 0]
    candidatos.sort(key=_contribuicao, reverse=True)
    return candidatos[:3]


def _buscar_detalhamento_com_fallback(mes_referencia_esperado, grupos):
    """Detalha por item os 3 grupos que mais pressionaram o IPCA para cima
    (maior variação × peso, só grupos com variação positiva). Chamada HTTP
    independente da composição por grupo — nunca propaga exceção nem
    bloqueia a mensagem principal (mesmo padrão de
    _buscar_composicao_com_fallback)."""
    top3 = _top3_grupos_que_mais_subiram(grupos)
    if not top3:
        return None

    try:
        mes_itens, itens_por_grupo = buscar_itens_por_grupo()
    except Exception as exc:
        logger.warning("Detalhamento por item indisponível — omitindo da mensagem: %s", exc)
        return None

    if mes_itens != mes_referencia_esperado:
        logger.warning(
            "Detalhamento por item (%s) não bate com o mês do IPCA geral (%s) — omitindo",
            mes_itens, mes_referencia_esperado,
        )
        return None

    return [(grupo, itens_por_grupo.get(NUMERO_GRUPO[grupo.nome], [])) for grupo in top3]


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


def _montar_tabela_itens(itens):
    largura = max(len("Item"), max(len(item.nome) for item in itens)) + 2
    linhas = [f"{'Item':<{largura}}{'Var%':>7}{'Peso%':>7}"]
    for item in sorted(itens, key=_contribuicao, reverse=True):
        linhas.append(f"{item.nome:<{largura}}{_fmt(item.variacao_mensal):>7}{_fmt(item.peso_mensal):>7}")
    return "\n".join(linhas)


def _montar_detalhamento(detalhamento):
    linhas = ["\n*Grupos que mais pressionaram o IPCA para cima*:"]
    for grupo, itens in detalhamento:
        tabela = _montar_tabela_itens(itens)
        linhas.append(
            f"\n*{grupo.nome}*: {_fmt(grupo.variacao_mensal)}% (peso {_fmt(grupo.peso_mensal)}%)"
            f"\n\n```\n{tabela}\n```"
        )
    return "\n".join(linhas)


def _montar_mensagem(mes_anterior, atual, mes_ano_anterior, grupos, detalhamento):
    variacao_anualizada = calcular_variacao_anualizada(atual.variacao_mensal)
    linhas = [
        f"📈 *IPCA — {atual.mes_referencia}*",
        "",
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
        linhas.append(f"\n*Composição por grupo*:\n\n```\n{tabela}\n```")
    if detalhamento is not None:
        linhas.append(_montar_detalhamento(detalhamento))
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
    detalhamento = _buscar_detalhamento_com_fallback(atual.mes_referencia, grupos) if grupos is not None else None
    mensagem = _montar_mensagem(mes_anterior_api, atual, mes_ano_anterior, grupos, detalhamento)

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
