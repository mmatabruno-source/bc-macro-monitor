"""Script manual único para achar a sintaxe correta de consulta OData4 do
IPEADATA (Metadados, filtro por SERNOME). Remover após o teste."""

import requests

BASE = "http://www.ipeadata.gov.br/api/odata4/Metadados"

VARIANTES = [
    ("sem $format", f"{BASE}?$filter=contains(SERNOME,'IPCA')"),
    ("$format=json", f"{BASE}?$filter=contains(SERNOME,'IPCA')&$format=json"),
    ("$format=application/json", f"{BASE}?$filter=contains(SERNOME,'IPCA')&$format=application/json"),
    ("com $select e $top", f"{BASE}?$filter=contains(SERNOME,'IPCA')&$select=SERCODIGO,SERNOME,PERNOME&$top=50"),
    ("aspas duplas", f'{BASE}?$filter=contains(SERNOME,"IPCA")'),
]


def main():
    for nome, url in VARIANTES:
        print(f"\n=== {nome} ===")
        print(url)
        try:
            resposta = requests.get(url, timeout=15, headers={"Accept": "application/json"})
            print(f"status_code={resposta.status_code}")
            print(resposta.text[:1500])
        except Exception as exc:
            print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
