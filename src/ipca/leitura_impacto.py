"""Regra determinística de leitura de impacto para portfólio (FR-009, sem LLM).

META_INFLACAO_CENTRO é um parâmetro de política definido anualmente pelo CMN
por resolução, não por uma API com atualização contínua — revisar
manualmente quando o CMN divulgar a meta de um novo ano (ver research.md, R3).
"""

from src.ipca.modelos import LeituraImpactoIpca

META_INFLACAO_CENTRO = 3.0  # % ao ano


def gerar_leitura(mes_anterior, mes_atual):
    if mes_atual.variacao_mensal > mes_anterior.variacao_mensal:
        direcao = "acelerou"
    elif mes_atual.variacao_mensal < mes_anterior.variacao_mensal:
        direcao = "desacelerou"
    else:
        direcao = "estavel"

    variacao_anualizada = mes_atual.variacao_mensal * 12
    if variacao_anualizada > META_INFLACAO_CENTRO:
        posicao = "acima"
    elif variacao_anualizada < META_INFLACAO_CENTRO:
        posicao = "abaixo"
    else:
        posicao = "em_linha"

    return LeituraImpactoIpca(direcao_vs_mes_anterior=direcao, posicao_vs_meta=posicao)
