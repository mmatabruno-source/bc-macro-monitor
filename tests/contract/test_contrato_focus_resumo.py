"""Contract test do parser do resumo semanal do Focus, usando o payload
real verificado.

Payload real: tests/fixtures/expectativas_anuais_2026-06-26.json
(ver specs/004-focus-resumo-semanal/contracts/expectativas-anuais.md)
"""

import json
from pathlib import Path

from src.focus_resumo.cliente_expectativas_anuais import _parse_valores

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "expectativas_anuais_2026-06-26.json"


def test_parse_extrai_indicadores_e_anos():
    payload = json.loads(FIXTURE.read_text())

    valores = _parse_valores(payload["value"], anos=["2026", "2027", "2028", "2029", "2030"])

    assert len(valores) == 20  # 4 indicadores x 5 anos
    indicadores = {v.indicador for v in valores}
    assert indicadores == {"IPCA", "Selic", "Câmbio", "PIB Total"}


def test_parse_valor_especifico():
    payload = json.loads(FIXTURE.read_text())

    valores = _parse_valores(payload["value"], anos=["2026"])

    selic_2026 = next(v for v in valores if v.indicador == "Selic" and v.ano == "2026")
    assert selic_2026.valor == 14.0000


def test_parse_filtra_apenas_anos_pedidos():
    payload = json.loads(FIXTURE.read_text())

    valores = _parse_valores(payload["value"], anos=["2026", "2027"])

    anos = {v.ano for v in valores}
    assert anos == {"2026", "2027"}
