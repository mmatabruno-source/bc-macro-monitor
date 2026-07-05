import json
from unittest.mock import patch

import pytest

from src.comum.isolamento import _executar_isolado
from src.ipca.fluxo import processar
from src.ipca.modelos import DivulgacaoIpca, GrupoIpca


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.ipca.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.ipca.fluxo.HISTORICO_DIR", tmp_path / "historico" / "ipca")
    monkeypatch.setenv("IPCA_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("IPCA_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


GRUPOS_FAKE = [
    GrupoIpca(nome="Alimentação e bebidas", variacao_mensal=1.33, peso_mensal=21.5939),
    GrupoIpca(nome="Transportes", variacao_mensal=-0.46, peso_mensal=20.4854),
]

ITENS_FAKE = {
    1: [GrupoIpca(nome="Cereais, leguminosas e oleaginosas", variacao_mensal=2.55, peso_mensal=0.7109)],
}


def _serie_13_meses(valor_mes_ano_anterior=0.44):
    """13 meses consecutivos, 2025-05 (mais antigo) até 2026-05 (atual),
    na ordem esperada da API (mais antigo primeiro)."""
    divulgacoes = [DivulgacaoIpca(mes_referencia="2025-05", variacao_mensal=valor_mes_ano_anterior)]
    for mes in range(6, 13):
        divulgacoes.append(DivulgacaoIpca(mes_referencia=f"2025-{mes:02d}", variacao_mensal=0.5))
    for mes in range(1, 4):
        divulgacoes.append(DivulgacaoIpca(mes_referencia=f"2026-{mes:02d}", variacao_mensal=0.5))
    divulgacoes.append(DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67))
    divulgacoes.append(DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58))
    assert len(divulgacoes) == 13
    return divulgacoes


def test_primeiro_mes_notifica(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", return_value=("2026-05", ITENS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    mock_enviar.assert_called_once()
    texto = mock_enviar.call_args.args[0]
    assert "2026-05" in texto
    assert "0,58" in texto
    assert "Composição por grupo" in texto
    assert "Alimentação e bebidas" in texto
    assert "-0,46" in texto
    assert "21,59" in texto
    assert "Grupos que mais pressionaram o IPCA para cima" in texto
    assert "Cereais, leguminosas e oleaginosas" in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_ipca"]["mes_referencia"] == "2026-05"


def test_mostra_mes_do_ano_anterior_quando_disponivel(estado_path):
    divulgacoes = _serie_13_meses(valor_mes_ano_anterior=0.44)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=divulgacoes), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", return_value=("2026-05", ITENS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processar()

    texto = mock_enviar.call_args.args[0]
    assert "Mês do ano anterior" in texto
    assert "0,44" in texto


def test_omite_mes_do_ano_anterior_se_api_nao_retornar_13_meses(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", return_value=("2026-05", ITENS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processar()

    texto = mock_enviar.call_args.args[0]
    assert "Mês do ano anterior" not in texto


def test_mesmo_mes_relido_nao_notifica_idempotencia(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_ipca": {"mes_referencia": "2026-05", "variacao_mensal": 0.58}
    }))
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


def test_falha_na_composicao_envia_mensagem_sem_tabela(estado_path):
    """A composição por grupo (IBGE) é instável em produção — ver
    specs/003-ipca-mensal/decisoes/composicao-ipca-por-grupo.md. Uma falha
    nela nunca pode bloquear o alerta principal do IPCA (BC/SGS, confiável)."""
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", side_effect=RuntimeError("ConnectTimeout")), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "2026-05" in texto
    assert "0,58" in texto
    assert "Composição por grupo" not in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_ipca"]["mes_referencia"] == "2026-05"


def test_mes_da_composicao_divergente_envia_mensagem_sem_tabela(estado_path):
    """Se o IBGE ainda não publicou a composição do mês mais recente do
    IPCA geral (BC), não mostra uma tabela de mês errado silenciosamente."""
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-04", 0.67, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "Composição por grupo" not in texto


def test_detalhamento_omitido_quando_busca_itens_falha(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", side_effect=RuntimeError("ConnectTimeout")), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "Composição por grupo" in texto
    assert "Grupos que mais pressionaram o IPCA para cima" not in texto


def test_detalhamento_omitido_quando_mes_dos_itens_diverge(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", return_value=("2026-04", ITENS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "Grupos que mais pressionaram o IPCA para cima" not in texto


def test_sem_grupo_positivo_nao_gera_detalhamento(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)
    grupos_todos_negativos = [
        GrupoIpca(nome="Alimentação e bebidas", variacao_mensal=-1.33, peso_mensal=21.5939),
        GrupoIpca(nome="Transportes", variacao_mensal=-0.46, peso_mensal=20.4854),
    ]

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, grupos_todos_negativos)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo") as mock_buscar_itens, \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    mock_buscar_itens.assert_not_called()
    texto = mock_enviar.call_args.args[0]
    assert "Grupos que mais pressionaram o IPCA para cima" not in texto


def test_top3_grupos_selecionados_por_variacao_vezes_peso():
    from src.ipca.fluxo import _top3_grupos_que_mais_subiram

    grupos = [
        GrupoIpca(nome="A", variacao_mensal=1.0, peso_mensal=10.0),   # contrib 10
        GrupoIpca(nome="B", variacao_mensal=0.5, peso_mensal=50.0),   # contrib 25
        GrupoIpca(nome="C", variacao_mensal=2.0, peso_mensal=1.0),    # contrib 2
        GrupoIpca(nome="D", variacao_mensal=-5.0, peso_mensal=30.0),  # negativo, fora
        GrupoIpca(nome="E", variacao_mensal=0.9, peso_mensal=20.0),   # contrib 18
    ]

    top3 = _top3_grupos_que_mais_subiram(grupos)

    assert [g.nome for g in top3] == ["B", "E", "A"]


def test_falha_no_envio_ao_telegram_nao_grava_estado(estado_path):
    """Princípio V (idempotência): falha ao notificar não pode ser
    confundida com falha ao processar — o estado deve permanecer como
    "não processado" para a próxima execução tentar de novo."""
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)
    estado_original = estado_path.read_text()

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
         patch("src.ipca.fluxo.buscar_itens_por_grupo", return_value=("2026-05", ITENS_FAKE)), \
         patch("src.ipca.fluxo.enviar_mensagem", side_effect=RuntimeError("Telegram fora do ar")):
        resultado = _executar_isolado("IPCA", processar)

    assert resultado["falhou"] is True
    assert estado_path.read_text() == estado_original


def test_falha_na_checagem_e_isolada_e_nao_altera_estado(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_ipca": {"mes_referencia": "2026-04", "variacao_mensal": 0.67}
    }))
    estado_original = estado_path.read_text()

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", side_effect=RuntimeError("série indisponível")):
        resultado = _executar_isolado("IPCA", processar)

    assert resultado["falhou"] is True
    assert resultado["processado"] is False
    assert estado_path.read_text() == estado_original
