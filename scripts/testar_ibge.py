"""Script manual único para comparar acesso real, a partir do runner do
GitHub Actions, entre apisidra.ibge.gov.br (bloqueado, connect timeout) e
servicodados.ibge.gov.br (API v3 de Agregados, teste de alternativa).
Remover após o teste."""

import requests

URL_V3 = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/7060/periodos/-1/"
    "variaveis/63|66?localidades=N1[all]&classificacao=315[7169,7170,7445,7486,7558,7625,7660,7712,7766,7786]"
)


def main():
    print(f"Testando: {URL_V3}")
    try:
        resposta = requests.get(URL_V3, timeout=20)
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:2000])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
