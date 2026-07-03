"""Testes unitários do fallback FR-006: falha na análise não impede o
relatório de ser considerado processado (o aviso já foi enviado)."""

import json
from unittest.mock import patch

import pytest

from src.relatorio.fluxo import processar
from src.relatorio.modelos import RelatorioPoliticaMonetaria


@pytest.fixture
def estado_path(tmp_path, monkeypatch):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{}")
    monkeypatch.setattr("src.comum.estado.ESTADO_PATH", caminho)
    monkeypatch.setattr("src.relatorio.fluxo.ESTADO_PATH", caminho)
    monkeypatch.setenv("RELATORIO_TELEGRAM_BOT_TOKEN", "token-fake")
    monkeypatch.setenv("RELATORIO_TELEGRAM_CHAT_ID", "chat-fake")
    return caminho


def test_falha_no_download_do_pdf_ainda_marca_processado(estado_path):
    atual = RelatorioPoliticaMonetaria(
        identificador="202412",
        data_publicacao="2024-12-19",
        link_pdf="https://exemplo.com/relatorio.pdf",
        link_pagina="https://exemplo.com/pagina",
    )

    with patch("src.relatorio.fluxo.buscar_relatorio_mais_recente", return_value=atual), \
         patch("src.relatorio.fluxo.gerar_analise", side_effect=ConnectionError("timeout")), \
         patch("src.relatorio.fluxo.enviar_mensagem") as mock_enviar:
        processado = processar()

    assert processado is True
    assert mock_enviar.call_count == 1  # só o aviso

    dados = json.loads(estado_path.read_text())
    assert dados["ultimo_relatorio"]["identificador"] == "202412"
