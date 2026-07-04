"""Contract test do parser da tabela SIDRA 7060 (composição do IPCA por grupo),
usando o payload real verificado.

Payload real: tests/fixtures/ipca_composicao_2026-05.json
"""

import json
from pathlib import Path

from src.ipca.cliente_composicao import CODIGOS_GRUPOS, _parse_payload

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "ipca_composicao_2026-05.json"


def test_parse_extrai_mes_referencia_e_variacao_do_indice_geral():
    payload = json.loads(FIXTURE.read_text())

    mes_referencia, variacao_indice_geral, grupos = _parse_payload(payload)

    assert mes_referencia == "2026-05"
    assert variacao_indice_geral == 0.58


def test_parse_extrai_os_9_grupos_na_ordem_oficial():
    payload = json.loads(FIXTURE.read_text())

    _mes, _variacao, grupos = _parse_payload(payload)

    assert len(grupos) == 9
    assert [grupo.nome for grupo in grupos] == list(CODIGOS_GRUPOS.values())
    assert grupos[0].nome == "Alimentação e bebidas"
    assert grupos[0].variacao_mensal == 1.33
    assert grupos[0].peso_mensal == 21.5939
    assert grupos[4].nome == "Transportes"
    assert grupos[4].variacao_mensal == -0.46
