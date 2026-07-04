"""Script manual único para validar visualmente o formato da mensagem do
fluxo Focus/Copom, enviando os 3 cenários (corte, manutenção, alta) com
dados fictícios. Não faz parte do pipeline; remover após o teste."""

import os

from src.comum.telegram import enviar_mensagem
from src.focus.comparador import DivulgacaoFocus
from src.focus.fluxo import _montar_mensagem

CENARIOS = [
    ("Corte", DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.0), 14.25),
    ("Manutenção", DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.25), 14.25),
    ("Alta", DivulgacaoFocus(reuniao_id="R5/2026", data_referencia="2026-06-26", mediana_selic=14.5), 14.25),
]


def main():
    token = os.environ["FOCUS_TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["FOCUS_TELEGRAM_CHAT_ID"]

    for nome, atual, selic_vigente in CENARIOS:
        mensagem = _montar_mensagem(atual, selic_vigente)
        print(f"Enviando cenário: {nome}")
        enviar_mensagem(mensagem, token, chat_id)


if __name__ == "__main__":
    main()
