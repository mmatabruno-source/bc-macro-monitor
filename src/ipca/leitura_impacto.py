"""Cálculo de variação anualizada do IPCA e meta de inflação vigente.

META_INFLACAO_CENTRO é um parâmetro de política definido anualmente pelo CMN
por resolução, não por uma API com atualização contínua — revisar
manualmente quando o CMN divulgar a meta de um novo ano (ver research.md, R3).
"""

META_INFLACAO_CENTRO = 3.0  # % ao ano


def calcular_variacao_anualizada(variacao_mensal):
    """Projeta a variação mensal para 12 meses por juros compostos:
    ((1 + variacao_mensal/100)^12 - 1) * 100."""
    return ((1 + variacao_mensal / 100) ** 12 - 1) * 100
