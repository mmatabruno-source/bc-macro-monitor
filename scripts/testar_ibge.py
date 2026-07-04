"""Script manual único para explorar o catálogo de séries do IPEADATA e ver
se existe a composição do IPCA por grupo (com peso), a partir do runner do
GitHub Actions. Remover após o teste."""

import requests

URL_METADADOS = (
    "http://www.ipeadata.gov.br/api/odata4/Metadados"
    "?$filter=contains(SERNOME,'IPCA')&$format=json"
)


def main():
    print(f"Testando: {URL_METADADOS}")
    try:
        resposta = requests.get(URL_METADADOS, timeout=20)
        print(f"status_code={resposta.status_code}")
        dados = resposta.json()
        valores = dados.get("value", dados)
        print(f"Total de séries encontradas: {len(valores)}")
        for serie in valores:
            print(f"  {serie.get('SERCODIGO')}: {serie.get('SERNOME')} (fonte={serie.get('FNTNOME')}, periodicidade={serie.get('PERNOME')})")
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
