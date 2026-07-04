"""Lógica de comparação subiu/desceu/manteve para o Resumo Semanal do Focus.

Sem contador de sequência (FR-006) — só a direção da última comparação.
"""


def _chave(valor_item):
    return f"{valor_item.indicador}:{valor_item.ano}"


def comparar_valores(valores_anteriores, valores_atuais):
    """valores_anteriores: dict "{indicador}:{ano}" -> valor (do estado).
    valores_atuais: list[ValorIndicadorAno].

    Retorna dict "{indicador}:{ano}" -> 'subiu'|'desceu'|'manteve'|None
    (None quando não há valor anterior registrado para aquele item)."""
    direcoes = {}
    for item in valores_atuais:
        chave = _chave(item)
        anterior = valores_anteriores.get(chave)
        if anterior is None:
            direcoes[chave] = None
        elif item.valor > anterior:
            direcoes[chave] = "subiu"
        elif item.valor < anterior:
            direcoes[chave] = "desceu"
        else:
            direcoes[chave] = "manteve"
    return direcoes
