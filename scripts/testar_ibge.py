"""Script manual único para validar o cliente_composicao (API v3 do IBGE)
com dados reais, a partir do runner do GitHub Actions. Remover após o teste."""

from src.ipca.cliente_composicao import buscar_composicao_ipca


def main():
    mes, variacao_geral, grupos = buscar_composicao_ipca()
    print(f"mes_referencia={mes} variacao_geral={variacao_geral}")
    for grupo in grupos:
        print(f"  {grupo.nome}: variacao={grupo.variacao_mensal} peso={grupo.peso_mensal}")


if __name__ == "__main__":
    main()
