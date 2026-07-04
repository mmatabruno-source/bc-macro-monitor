"""Script manual único para achar a sintaxe correta de consulta OData4 do
IPEADATA (Metadados, filtro por SERNOME). Remover após o teste."""

import requests

BASE = "http://www.ipeadata.gov.br/api/odata4/Metadados"

VARIANTES = [
    ("substringof (OData v2/v3)", f"{BASE}?$filter=substringof('IPCA',SERNOME)"),
    ("sem filtro, só $top", f"{BASE}?$top=3"),
    ("filtro por igualdade em SERCODIGO conhecido", f"{BASE}?$filter=SERCODIGO eq 'PRECOS12_IPCA12'"),
    ("startswith", f"{BASE}?$filter=startswith(SERNOME,'IPCA')"),
    ("aspas simples com espaco codificado", f"{BASE}?%24filter=contains(SERNOME%2C%27IPCA%27)"),
]


def main():
    for nome, url in VARIANTES:
        print(f"\n=== {nome} ===")
        print(url)
        try:
            resposta = requests.get(url, timeout=15, headers={"Accept": "application/json"})
            print(f"status_code={resposta.status_code}")
            print(resposta.text[:2000])
        except Exception as exc:
            print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
