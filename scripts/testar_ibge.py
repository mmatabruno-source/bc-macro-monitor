"""Script manual único para medir confiabilidade real, a partir do runner do
GitHub Actions, de apisidra.ibge.gov.br vs servicodados.ibge.gov.br (API v3).
Faz múltiplas tentativas em cada host. Remover após o teste."""

import time

import requests

URL_APISIDRA = (
    "https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63,66/p/last%201/"
    "c315/7169,7170,7445,7486,7558,7625,7660,7712,7766,7786?formato=json"
)
URL_SERVICODADOS = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-1/"
    "variaveis/63|66?localidades=N1[all]&classificacao=315[7169,7170,7445,7486,7558,7625,7660,7712,7766,7786]"
)


def testar(nome, url, tentativas=5, timeout=10):
    print(f"\n=== {nome} ===")
    for i in range(1, tentativas + 1):
        inicio = time.monotonic()
        try:
            resposta = requests.get(url, timeout=timeout)
            duracao = time.monotonic() - inicio
            print(f"tentativa {i}: status={resposta.status_code} duracao={duracao:.2f}s")
        except Exception as exc:
            duracao = time.monotonic() - inicio
            print(f"tentativa {i}: FALHOU ({type(exc).__name__}) duracao={duracao:.2f}s")
        time.sleep(2)


def main():
    testar("apisidra.ibge.gov.br", URL_APISIDRA)
    testar("servicodados.ibge.gov.br", URL_SERVICODADOS)


if __name__ == "__main__":
    main()
