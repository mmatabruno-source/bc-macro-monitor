import json
from unittest.mock import patch

import pytest

from src.comum.isolamento import _executar_isolado
from src.relatorio.fluxo import processar
from src.relatorio.modelos import AnaliseCritica, RelatorioPoliticaMonetaria


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.relatorio.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.relatorio.fluxo.HISTORICO_DIR", tmp_path / "historico" / "relatorios")
    monkeypatch.setenv("RELATORIO_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("RELATORIO_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


def _relatorio(identificador="202412"):
    return RelatorioPoliticaMonetaria(
        identificador=identificador,
        data_publicacao="2024-12-19",
        link_pdf="https://www.bcb.gov.br/content/ri/relatorioinflacao/202412/ri202412p.pdf",
        link_pagina="https://www.bcb.gov.br/publicacoes/ri/202412",
    )


def test_novo_relatorio_envia_aviso_e_analise(estado_path):
    atual = _relatorio()
    analise = AnaliseCritica(
        visao_cidadao="▪️ visão cidadão X",
        visao_investidor="▪️ visão investidor Y",
    )

    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", return_value=atual), \
         patch("src.relatorio.fluxo.gerar_analise", return_value=analise), \
         patch("src.relatorio.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    assert mock_enviar.call_count == 3
    textos = [chamada.args[0] for chamada in mock_enviar.call_args_list]
    assert any(atual.link_pagina in texto for texto in textos)
    assert any("visão cidadão X" in texto for texto in textos)
    assert any("visão investidor Y" in texto for texto in textos)

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_relatorio"]["identificador"] == "202412"


def test_relatorio_ja_processado_nao_notifica(estado_path):
    estado_path.write_text(json.dumps({"ultimo_relatorio": {"identificador": "202412"}}))
    atual = _relatorio()

    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", return_value=atual), \
         patch("src.relatorio.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is False
    mock_enviar.assert_not_called()


def test_falha_na_analise_envia_apenas_aviso(estado_path):
    atual = _relatorio()

    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", return_value=atual), \
         patch("src.relatorio.fluxo.gerar_analise", side_effect=RuntimeError("PDF inválido")), \
         patch("src.relatorio.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    mock_enviar.assert_called_once()
    texto = mock_enviar.call_args.args[0]
    assert atual.link_pagina in texto

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_relatorio"]["identificador"] == "202412"


def test_falha_no_envio_do_aviso_nao_grava_estado(estado_path):
    """Princípio V (idempotência): se o aviso de publicação (mensagem
    sempre enviada) falhar, o estado não pode ser gravado como
    processado — nem a análise crítica deve ser tentada."""
    atual = _relatorio()
    estado_original = estado_path.read_text()

    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", return_value=atual), \
         patch("src.relatorio.fluxo.gerar_analise") as mock_gerar_analise, \
         patch("src.relatorio.fluxo.enviar_mensagem", side_effect=RuntimeError("Telegram fora do ar")):
        resultado = _executar_isolado("Relatório", processar)

    assert resultado["falhou"] is True
    assert estado_path.read_text() == estado_original
    mock_gerar_analise.assert_not_called()


def test_falha_na_checagem_do_dataset_e_isolada(estado_path):
    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", side_effect=RuntimeError("dataset indisponível")):
        resultado = _executar_isolado("Relatório", processar)

    assert resultado["falhou"] is True
    assert resultado["processado"] is False

    dados = json.loads(estado_path.read_text())
    assert dados == {}
