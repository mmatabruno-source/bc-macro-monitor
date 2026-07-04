"""Ponto de entrada único do GitHub Actions: executa cada fluxo isoladamente."""

import logging
import os

from src.comum.isolamento import _executar_isolado, notificar_falha
from src.focus.fluxo import processar as processar_focus
from src.focus_resumo.fluxo import processar as processar_focus_resumo
from src.ipca.fluxo import processar as processar_ipca
from src.relatorio.fluxo import processar as processar_relatorio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    resultado_focus = _executar_isolado("Focus/Copom", processar_focus)
    if resultado_focus["falhou"]:
        notificar_falha(
            "processamento inesperado do fluxo Focus/Copom",
            resultado_focus["erro"],
            token=os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN"),
            chat_id=os.environ.get("FOCUS_TELEGRAM_CHAT_ID"),
        )

    resultado_ipca = _executar_isolado("IPCA", processar_ipca)
    if resultado_ipca["falhou"]:
        notificar_falha(
            "processamento inesperado do fluxo IPCA",
            resultado_ipca["erro"],
            token=os.environ.get("IPCA_TELEGRAM_BOT_TOKEN"),
            chat_id=os.environ.get("IPCA_TELEGRAM_CHAT_ID"),
        )

    resultado_relatorio = _executar_isolado("Relatório de Política Monetária", processar_relatorio)
    if resultado_relatorio["falhou"]:
        notificar_falha(
            "processamento inesperado do fluxo Relatório de Política Monetária",
            resultado_relatorio["erro"],
            token=os.environ.get("RELATORIO_TELEGRAM_BOT_TOKEN"),
            chat_id=os.environ.get("RELATORIO_TELEGRAM_CHAT_ID"),
        )

    resultado_focus_resumo = _executar_isolado("Resumo Semanal do Focus", processar_focus_resumo)
    if resultado_focus_resumo["falhou"]:
        notificar_falha(
            "processamento inesperado do resumo semanal do Focus",
            resultado_focus_resumo["erro"],
            token=os.environ.get("FOCUS_TELEGRAM_BOT_TOKEN"),
            chat_id=os.environ.get("FOCUS_TELEGRAM_CHAT_ID"),
        )


if __name__ == "__main__":
    main()
