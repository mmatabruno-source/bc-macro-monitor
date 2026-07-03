"""Lógica de comparação subiu/desceu/manteve/inicial para o fluxo Focus."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DivulgacaoFocus:
    reuniao_id: str
    data_referencia: str
    mediana_selic: float


def comparar(anterior, atual):
    """Retorna 'inicial', 'subiu', 'desceu' ou 'manteve'.

    'inicial': sem baseline anterior, ou troca de reunião monitorada (FR-008).
    """
    if anterior is None or anterior.reuniao_id != atual.reuniao_id:
        return "inicial"
    if atual.mediana_selic > anterior.mediana_selic:
        return "subiu"
    if atual.mediana_selic < anterior.mediana_selic:
        return "desceu"
    return "manteve"
