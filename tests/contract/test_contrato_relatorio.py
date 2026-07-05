"""Contract test do parser do dataset de Relatórios de Política Monetária,
usando o payload real verificado.

Payload real: tests/fixtures/relatorios_rpm_quantidade_5.json
(ver specs/002-relatorio-politica-monetaria/contracts/relatorio-dataset.md)
"""

import json
from pathlib import Path

from src.relatorio.cliente_dataset import _parse_relatorios

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "relatorios_rpm_quantidade_5.json"


def test_parse_extrai_relatorio_mais_recente_primeiro():
    payload = json.loads(FIXTURE.read_text())

    relatorios = _parse_relatorios(payload)

    assert len(relatorios) == 5
    assert relatorios[0].identificador == "202606"
    assert relatorios[0].data_publicacao == "2026-06-25"
    assert relatorios[0].link_pdf.endswith("rpm202606p.pdf")
    assert relatorios[0].link_pagina == "https://www.bcb.gov.br/publicacoes/rpm/202606"


def test_parse_ordem_mais_recente_para_mais_antigo():
    payload = json.loads(FIXTURE.read_text())

    relatorios = _parse_relatorios(payload)

    identificadores = [r.identificador for r in relatorios]
    assert identificadores == ["202606", "202603", "202512", "202509", "202506"]
