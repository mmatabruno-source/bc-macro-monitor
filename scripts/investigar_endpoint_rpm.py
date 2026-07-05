"""Script TEMPORÁRIO de investigação: o dataset atual usado pelo cliente
(`ri/relatorios`) está preso em 202412 — o documento foi renomeado de
"Relatório de Inflação" para "Relatório de Política Monetária" e o
dataset antigo parou de receber itens novos. Este script tenta variantes
plausíveis de endpoint/URL para achar a fonte atualizada, sem enviar
nada ao Telegram. Remover após o uso."""

import requests

CANDIDATOS = [
    "https://www.bcb.gov.br/api/servico/sitebcb/rpm/relatorios?quantidade=5",
    "https://www.bcb.gov.br/api/servico/sitebcb/ri/relatorios?quantidade=5",
    "https://www.bcb.gov.br/api/servico/sitebcb/relatoriopoliticamonetaria/relatorios?quantidade=5",
    "https://www.bcb.gov.br/api/servico/sitebcb/politicamonetaria/rpm?quantidade=5",
    "https://www.bcb.gov.br/publicacoes/rpm",
]


def main():
    for url in CANDIDATOS:
        print("=" * 80)
        print("URL:", url)
        try:
            resposta = requests.get(url, timeout=20)
            print("Status:", resposta.status_code)
            print("Content-Type:", resposta.headers.get("Content-Type"))
            texto = resposta.text
            print("Primeiros 2000 chars:")
            print(texto[:2000])
        except Exception as exc:
            print("ERRO:", repr(exc))


if __name__ == "__main__":
    main()
