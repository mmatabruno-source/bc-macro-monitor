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

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_ipca"]["mes_referencia"] == "2026-05"


def test_mostra_mes_do_ano_anterior_quando_disponivel(estado_path):
    divulgacoes = _serie_13_meses(valor_mes_ano_anterior=0.44)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=divulgacoes), \
         patch("src.ipca.fluxo.buscar_composicao_ipca", return_value=("2026-05", 0.58, GRUPOS_FAKE)), \
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
