"""Script manual único para conferir os valores reais usados na última
mensagem do fluxo IPCA (13 meses da série 433 do BC). Remover após o teste."""

from src.ipca.cliente_sgs import buscar_ultimas_divulgacoes
from src.ipca.leitura_impacto import META_INFLACAO_CENTRO, calcular_variacao_anualizada


def main():
    divulgacoes = buscar_ultimas_divulgacoes(quantidade=13)
    for d in divulgacoes:
        print(d.mes_referencia, d.variacao_mensal)

    atual = divulgacoes[-1]
    print(f"\natual={atual.mes_referencia} variacao_mensal={atual.variacao_mensal}")
    print(f"mes_anterior={divulgacoes[-2].mes_referencia} variacao={divulgacoes[-2].variacao_mensal}")
    print(f"mes_ano_anterior={divulgacoes[-13].mes_referencia} variacao={divulgacoes[-13].variacao_mensal}")
    print(f"variacao_anualizada={calcular_variacao_anualizada(atual.variacao_mensal):.2f}")
    print(f"meta={META_INFLACAO_CENTRO}")


if __name__ == "__main__":
    main()
