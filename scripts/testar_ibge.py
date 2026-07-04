"""Script manual único para testar a sintaxe do IPEADATA usando o dicionário
`params=` do requests (deixando a lib codificar a URL corretamente), igual
aos projetos reais (brazilvisible, OpenFinData) que usam essa API com
sucesso. Remover após o teste."""

import requests

BASE = "http://www.ipeadata.gov.br/api/odata4/Metadados"


def main():
    print("=== via params= (requests codifica) ===")
    try:
        resposta = requests.get(
            BASE,
            params={
                "$top": 20,
                "$filter": "contains(SERNOME,'IPCA')",
                "$select": "SERCODIGO,SERNOME,PERNOME,UNINOME",
            },
            timeout=15,
        )
        print(f"url final: {resposta.url}")
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:3000])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")

    print("\n=== com espaço depois da vírgula no contains ===")
    try:
        resposta = requests.get(
            BASE,
            params={
                "$top": 20,
                "$filter": "contains(SERNOME, 'IPCA')",
            },
            timeout=15,
        )
        print(f"url final: {resposta.url}")
        print(f"status_code={resposta.status_code}")
        print(resposta.text[:3000])
    except Exception as exc:
        print(f"FALHOU: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
