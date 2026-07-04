"""Contract test do parser da série 433 (IPCA), usando o payload real verificado.

Payload real: tests/fixtures/ipca_ultimos_3.json
(ver specs/003-ipca-mensal/contracts/ipca-sgs.md)
"""

import json
from pathlib import Path

from src.ipca.cliente_sgs import _parse_divulgacoes

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "ipca_ultimos_3.json"


def test_parse_extrai_mes_referencia_e_variacao():
    payload = json.loads(FIXTURE.read_text())

    divulgacoes = _parse_divulgacoes(payload)

    assert len(divulgacoes) == 3
    assert divulgacoes[0].mes_referencia == "2026-03"
    assert divulgacoes[0].variacao_mensal == 0.88
    assert divulgacoes[1].mes_referencia == "2026-04"
    assert divulgacoes[2].mes_referencia == "2026-05"
    assert divulgacoes[2].variacao_mensal == 0.58


def test_ultimo_elemento_e_o_mes_mais_recente():
    payload = json.loads(FIXTURE.read_text())

    divulgacoes = _parse_divulgacoes(payload)

    assert divulgacoes[-1].mes_referencia == "2026-05"
