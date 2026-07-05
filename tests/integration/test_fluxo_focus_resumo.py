import json
from unittest.mock import patch

import pytest

from src.comum.isolamento import _executar_isolado
from src.focus_resumo.fluxo import processar
from src.focus_resumo.modelos import DivulgacaoFocusResumo, ValorIndicadorAno


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.focus_resumo.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.focus_resumo.fluxo.HISTORICO_DIR", tmp_path / "historico" / "focus_resumo")
    monkeypatch.setenv("FOCUS_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("FOCUS_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


def _divulgacao(data_referencia, selic_2026):
    return DivulgacaoFocusResumo(
        data_referencia=data_referencia,
        valores=[
            ValorIndicadorAno(indicador="IPCA", ano="2026", valor=5.33),
            ValorIndicadorAno(indicador="Selic", ano="2026", valor=selic_2026),
            ValorIndicadorAno(indicador="Câmbio", ano="2026", valor=5.20),
            ValorIndicadorAno(indicador="PIB Total", ano="2026", valor=1.99),
        ],
    )


def test_primeira_divulgacao_sem_direcao(estado_path):
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_resumo_atual", return_value=atual), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "Selic" in texto
    assert "14,00%" in texto
    assert "Câmbio (BRL/USD)" in texto
    assert "PIB (var. sobre o ano anterior)" in texto
    assert "1,990%" in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_resumo_focus"]["data_referencia"] == "2026-06-26"


def test_nova_divulgacao_mostra_direcao(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_resumo_focus": {
            "data_referencia": "2026-06-19",
            "valores": {"IPCA:2026": 5.33, "Selic:2026": 14.0, "Câmbio:2026": 5.20, "PIB Total:2026": 1.99},
        }
    }))
    atual = _divulgacao("2026-06-26", 14.25)

    with patch("src.focus_resumo.fluxo.buscar_resumo_atual", return_value=atual), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "(▲ 0,25 p.p.)" in texto


def test_direcao_desceu_e_manteve(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_resumo_focus": {
            "data_referencia": "2026-06-19",
            "valores": {"IPCA:2026": 5.33, "Selic:2026": 14.25, "Câmbio:2026": 5.20, "PIB Total:2026": 1.99},
        }
    }))
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_resumo_atual", return_value=atual), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "(▼ 0,25 p.p.)" in texto
    assert "(= 0 p.p.)" in texto


def test_mesma_divulgacao_relida_nao_notifica(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_resumo_focus": {"data_referencia": "2026-06-26", "valores": {}}
    }))
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_resumo_atual", return_value=atual), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


def test_falha_na_checagem_e_isolada(estado_path):
    with patch("src.focus_resumo.fluxo.buscar_resumo_atual", side_effect=RuntimeError("API fora do ar")):
        resultado = _executar_isolado("Focus Resumo", processar)

    assert resultado["falhou"] is True
    assert resultado["processado"] is False

    dados = json.loads(estado_path.read_text())
    assert dados == {}
