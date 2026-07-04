"""Lógica de comparação para o fluxo Focus: Selic vigente vs. mediana
projetada pelo Focus para a próxima reunião do Copom."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DivulgacaoFocus:
    reuniao_id: str
    data_referencia: str
    mediana_selic: float


def calcular_variacao(selic_vigente, mediana_projetada):
    """Retorna (variacao_em_pp, emoji) da mediana projetada em relação à
    Selic vigente. Negativo = corte projetado, positivo = alta projetada."""
    variacao = round(mediana_projetada - selic_vigente, 2)
    if variacao < 0:
        emoji = "📉"
    elif variacao > 0:
        emoji = "📈"
    else:
        emoji = "➡️"
    return variacao, emoji
