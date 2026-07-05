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


def _buscar_divulgacao_fake(mapa):
    """Substitui src.focus_resumo.fluxo.buscar_divulgacao — retorna a
    divulgação correspondente à data pedida, a partir de um mapa
    {data: DivulgacaoFocusResumo}."""
    def _buscar(data_referencia):
        return mapa[data_referencia]
    return _buscar


def test_primeira_divulgacao_sem_direcao_quando_so_ha_uma_data(estado_path):
    """FR-005: sem uma segunda data disponível na API, não há como
    comparar — os valores aparecem sem direção."""
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26"]), \
         patch("src.focus_resumo.fluxo.buscar_divulgacao", side_effect=_buscar_divulgacao_fake({"2026-06-26": atual})), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "Selic" in texto
    assert "14,00%" in texto
    assert "Câmbio (BRL/USD)" in texto
    assert "PIB (var. sobre o ano anterior)" in texto
    assert "1,990%" in texto
    assert "▲" not in texto
    assert "▼" not in texto
    assert "= 0 p.p." not in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_resumo_focus"]["data_referencia"] == "2026-06-26"


def test_compara_sempre_contra_a_penultima_divulgacao_real_da_api(estado_path):
    """Requisito explícito do usuário: a comparação MUST vir de uma busca
    real da penúltima divulgação na API, nunca de estado local — mesmo
    que o estado.json local esteja vazio/ausente."""
    penultima = _divulgacao("2026-06-19", 14.0)
    atual = _divulgacao("2026-06-26", 14.25)

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26", "2026-06-19"]), \
         patch(
             "src.focus_resumo.fluxo.buscar_divulgacao",
             side_effect=_buscar_divulgacao_fake({"2026-06-26": atual, "2026-06-19": penultima}),
         ) as mock_buscar_divulgacao, \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    # As duas datas foram buscadas de fato (2 chamadas: atual + penúltima).
    assert mock_buscar_divulgacao.call_count == 2
    mock_buscar_divulgacao.assert_any_call("2026-06-26")
    mock_buscar_divulgacao.assert_any_call("2026-06-19")

    texto = mock_enviar.call_args.args[0]
    assert "(▲ 0,25 p.p.)" in texto


def test_direcao_desceu_e_manteve(estado_path):
    penultima = _divulgacao("2026-06-19", 14.25)
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26", "2026-06-19"]), \
         patch(
             "src.focus_resumo.fluxo.buscar_divulgacao",
             side_effect=_buscar_divulgacao_fake({"2026-06-26": atual, "2026-06-19": penultima}),
         ), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "(▼ 0,25 p.p.)" in texto
    assert "(= 0 p.p.)" in texto


def test_falha_ao_buscar_penultima_envia_mensagem_sem_comparacao(estado_path):
    """A busca da penúltima divulgação é um enriquecimento — se falhar,
    a mensagem principal ainda deve sair, só sem a direção."""
    atual = _divulgacao("2026-06-26", 14.0)

    def _buscar(data_referencia):
        if data_referencia == "2026-06-26":
            return atual
        raise RuntimeError("API fora do ar")

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26", "2026-06-19"]), \
         patch("src.focus_resumo.fluxo.buscar_divulgacao", side_effect=_buscar), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    texto = mock_enviar.call_args.args[0]
    assert "▲" not in texto
    assert "▼" not in texto
    assert "= 0 p.p." not in texto


def test_falha_no_envio_ao_telegram_nao_grava_estado(estado_path):
    """Princípio V (idempotência): falha ao notificar não pode ser
    confundida com falha ao processar — o estado deve permanecer como
    "não processado" para a próxima execução tentar de novo."""
    atual = _divulgacao("2026-06-26", 14.0)
    estado_original = estado_path.read_text()

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26"]), \
         patch("src.focus_resumo.fluxo.buscar_divulgacao", side_effect=_buscar_divulgacao_fake({"2026-06-26": atual})), \
         patch("src.focus_resumo.fluxo.enviar_mensagem", side_effect=RuntimeError("Telegram fora do ar")):
        resultado = _executar_isolado("Focus Resumo", processar)

    assert resultado["falhou"] is True
    assert estado_path.read_text() == estado_original


def test_mesma_divulgacao_relida_nao_notifica(estado_path):
    estado_path.write_text(json.dumps({
        "ultimo_resumo_focus": {"data_referencia": "2026-06-26", "valores": {}}
    }))
    atual = _divulgacao("2026-06-26", 14.0)

    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", return_value=["2026-06-26", "2026-06-19"]), \
         patch("src.focus_resumo.fluxo.buscar_divulgacao", side_effect=_buscar_divulgacao_fake({"2026-06-26": atual})), \
         patch("src.focus_resumo.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


def test_falha_na_checagem_e_isolada(estado_path):
    with patch("src.focus_resumo.fluxo.buscar_datas_recentes", side_effect=RuntimeError("API fora do ar")):
        resultado = _executar_isolado("Focus Resumo", processar)

    assert resultado["falhou"] is True
    assert resultado["processado"] is False

    dados = json.loads(estado_path.read_text())
    assert dados == {}
