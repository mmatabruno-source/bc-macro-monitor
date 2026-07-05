"""Script TEMPORÁRIO de investigação: o dataset atual usado pelo cliente
(`ri/relatorios`) está preso em 202412 — o documento foi renomeado de
"Relatório de Inflação" para "Relatório de Política Monetária" e o
dataset antigo parou de receber itens novos. Este script tenta variantes
plausíveis de endpoint/URL para achar a fonte atualizada, sem enviar
nada ao Telegram. Remover após o uso."""

import requests

URL = "https://www.bcb.gov.br/api/servico/sitebcb/rpm/relatorios?quantidade=5"


def main():
    print("URL:", URL)
    resposta = requests.get(URL, timeout=20)
    print("Status:", resposta.status_code)
    print("PAYLOAD COMPLETO:")
    print(resposta.text)


if __name__ == "__main__":
    main()
