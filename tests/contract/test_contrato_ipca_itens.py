"""Contract test do parser de itens da tabela SIDRA 7060 (classificacao=315[all]),
usando um payload real verificado com todos os níveis (grupo, subgrupo, item e subitem).

Payload real: tests/fixtures/ipca_itens_2026-05.json
"""

import json
from pathlib import Path

from src.ipca.cliente_composicao import _parse_payload_itens

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "ipca_itens_2026-05.json"


def test_parse_mantem_so_nivel_item_descartando_grupo_subgrupo_e_subitem():
    payload = json.loads(FIXTURE.read_text())

    mes_referencia, itens_por_grupo = _parse_payload_itens(payload)

    assert mes_referencia == "2026-05"
    nomes_grupo_1 = [item.nome for item in itens_por_grupo[1]]
    assert nomes_grupo_1 == ["Cereais, leguminosas e oleaginosas"]
    nomes_grupo_5 = [item.nome for item in itens_por_grupo[5]]
    assert nomes_grupo_5 == ["Transporte público"]


def test_parse_atribui_item_ao_grupo_pai_correto_e_com_valores_certos():
    payload = json.loads(FIXTURE.read_text())

    _mes, itens_por_grupo = _parse_payload_itens(payload)

    item = itens_por_grupo[1][0]
    assert item.variacao_mensal == 2.55
    assert item.peso_mensal == 0.7109

    item_transporte = itens_por_grupo[5][0]
    assert item_transporte.variacao_mensal == 0.85
    assert item_transporte.peso_mensal == 3.2211


def test_parse_retorna_lista_vazia_para_grupos_sem_item_no_payload():
    payload = json.loads(FIXTURE.read_text())

    _mes, itens_por_grupo = _parse_payload_itens(payload)

    assert itens_por_grupo[2] == []
