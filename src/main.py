"""Ponto de entrada único do GitHub Actions: executa cada fluxo isoladamente."""

import logging
import os

from src.comum.isolamento import _executar_isolado, notificar_falha
from src.focus.fluxo import processar as processar_focus

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

    # Fluxos 002 (Relatório de Política Monetária) e 003 (IPCA) serão
    # adicionados aqui quando suas respectivas features forem implementadas.


if __name__ == "__main__":
    main()
