import json
from unittest.mock import patch

import pytest

from src.comum.isolamento import _executar_isolado
from src.ipca.fluxo import processar
from src.ipca.modelos import DivulgacaoIpca


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


def test_primeiro_mes_notifica(estado_path):
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    mock_enviar.assert_called_once()
    texto = mock_enviar.call_args.args[0]
    assert "2026-05" in texto
    assert "0.58" in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_ipca"]["mes_referencia"] == "2026-05"


def test_mesmo_mes_relido_nao_notifica_idempotencia(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_ipca": {"mes_referencia": "2026-05", "variacao_mensal": 0.58}
    }))
    anterior = DivulgacaoIpca(mes_referencia="2026-04", variacao_mensal=0.67)
    atual = DivulgacaoIpca(mes_referencia="2026-05", variacao_mensal=0.58)

    with patch("src.ipca.fluxo.buscar_ultimas_divulgacoes", return_value=[anterior, atual]), \
         patch("src.ipca.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


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
