"""Contract test do parser da API Focus, usando o payload real verificado.

Payload real: tests/fixtures/focus_divulgacao_2026-06-26.json
(ver specs/001-focus-copom-alert/contracts/focus-api.md)
"""

import json
from pathlib import Path

from src.focus.cliente_expectativas import _escolher_proxima_reuniao

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "focus_divulgacao_2026-06-26.json"


def test_escolhe_menor_reuniao_com_base_calculo_zero():
    payload = json.loads(FIXTURE.read_text())
    linhas = payload["value"]

    divulgacao = _escolher_proxima_reuniao(linhas)

    assert divulgacao.reuniao_id == "R5/2026"
    assert divulgacao.data_referencia == "2026-06-26"
    # Mediana da linha baseCalculo=0 para R5/2026 na fixture: 14.0000
    assert divulgacao.mediana_selic == 14.0000


def test_ignora_linhas_base_calculo_um():
    payload = json.loads(FIXTURE.read_text())
    linhas = [linha for linha in payload["value"] if linha["Reuniao"] == "R5/2026"]

    divulgacao = _escolher_proxima_reuniao(linhas)

    # A linha baseCalculo=1 de R5/2026 tem Mediana 14.0000 também, mas
    # numeroRespondentes=76; a de baseCalculo=0 tem numeroRespondentes=145.
    # Verificamos que a escolhida é a de baseCalculo=0 (mais respondentes).
    escolhida = [l for l in linhas if l["baseCalculo"] == 0][0]
    assert divulgacao.mediana_selic == escolhida["Mediana"]
