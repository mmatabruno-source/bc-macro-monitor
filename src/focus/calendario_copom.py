"""Calendário oficial de reuniões do Copom.

Não existe API estruturada do BC para o calendário de reuniões futuras
(confirmado em pesquisa: só há API de atas já publicadas e uma página HTML
com o calendário do ano — https://www.bcb.gov.br/htms/copom_normas/copomcalend.asp).
Por isso este calendário é cadastrado manualmente e precisa ser atualizado
todo ano quando o BC publica o calendário do ano seguinte.
"""

from datetime import date

_MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

REUNIOES = {
    "R1/2026": (date(2026, 1, 27), date(2026, 1, 28)),
    "R2/2026": (date(2026, 3, 17), date(2026, 3, 18)),
    "R3/2026": (date(2026, 4, 28), date(2026, 4, 29)),
    "R4/2026": (date(2026, 6, 16), date(2026, 6, 17)),
    "R5/2026": (date(2026, 8, 4), date(2026, 8, 5)),
    "R6/2026": (date(2026, 9, 15), date(2026, 9, 16)),
    "R7/2026": (date(2026, 11, 3), date(2026, 11, 4)),
    "R8/2026": (date(2026, 12, 8), date(2026, 12, 9)),
}


def formatar_periodo_reuniao(reuniao_id):
    """'R5/2026' -> '4 a 5 de agosto'. Se a reunião ainda não estiver
    cadastrada no calendário (ex.: ano seguinte ainda não divulgado pelo BC),
    retorna o próprio identificador como fallback."""
    periodo = REUNIOES.get(reuniao_id)
    if periodo is None:
        return f"{reuniao_id} (data a definir)"

    inicio, fim = periodo
    if inicio.month == fim.month:
        return f"{inicio.day} a {fim.day} de {_MESES[inicio.month - 1]}"
    return f"{inicio.day} de {_MESES[inicio.month - 1]} a {fim.day} de {_MESES[fim.month - 1]}"
