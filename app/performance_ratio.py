"""
performance_ratio.py - Cálculo do PR (Performance Ratio), de forma explícita
sobre o que está sendo assumido.

Fórmula usada (a definição-padrão da IEC 61724):

    Yf = E_AC / P_nominal_kWp        (rendimento final, kWh/kWp)
    Yr = H_POA / G_STC               (horas de sol pleno, com G_STC = 1 kW/m2)
    PR = Yf / Yr

Decisões assumidas (documentadas aqui, não escondidas):
- P_nominal usado é 140 kWp (potência DC nominal dos módulos, conforme a
  proposta do projeto), e não os 119 kW AC (que é o limite de saída dos
  inversores, não a referência de STC dos módulos). Isso é uma escolha
  metodológica; o dashboard deixa essa escolha visível pro usuário.
- Quando as duas leituras de irradiância (LPPYRA02 e LPNET14) estão
  disponíveis, uso a média das duas. Não escolhi uma como "mais correta"
  porque não tenho informação de calibração de nenhuma delas.
- Só calculo PR para um dia se TODOS os intervalos de 15min daquele dia
  tiverem GHI disponível. Não calculo PR "parcial" com lacuna, porque isso
  distorceria o resultado sem aviso.
- Também não calculo se faltar potência da usina em algum intervalo com sol
  (GHI médio > 20 W/m2): tratar a lacuna como 0 kW subestimaria o PR.
"""

import pandas as pd

G_STC_W_M2 = 1000.0
P_NOMINAL_KWP = 140.0
INTERVALO_HORAS = 0.25  # 15 minutos
LIMIAR_SOL_W_M2 = 20.0  # abaixo disso considero "sem sol" (noite/crepúsculo)


def pr_calculavel(df_dia: pd.DataFrame) -> bool:
    """True só se o dia tem GHI em 100% dos registros de 15min."""
    if df_dia.empty:
        return False
    if not df_dia["ghi_disponivel"].all():
        return False
    # Se faltar potência da usina em horário de sol, somar "0" no lugar
    # derrubaria o PR sem aviso -- então também não calculo nesse caso.
    ghi_medio = df_dia[["ghi_lppyra02_w_m2", "ghi_lpnet14_w_m2"]].mean(axis=1)
    com_sol = ghi_medio > LIMIAR_SOL_W_M2
    return not df_dia.loc[com_sol, "potencia_fv_kw"].isna().any()


def calcular_pr(df_dia: pd.DataFrame) -> dict | None:
    """Recebe o DataFrame de leitura_15min de UM dia (já filtrado) e
    devolve um dicionário com o PR e os valores intermediários, ou None se
    não for possível calcular com confiança."""
    if not pr_calculavel(df_dia):
        return None

    df = df_dia.copy()
    df["ghi_medio_w_m2"] = df[["ghi_lppyra02_w_m2", "ghi_lpnet14_w_m2"]].mean(axis=1)

    energia_ac_kwh = df["potencia_fv_kw"].fillna(0).sum() * INTERVALO_HORAS
    insolacao_kwh_m2 = (df["ghi_medio_w_m2"] * INTERVALO_HORAS / 1000).sum()

    if insolacao_kwh_m2 <= 0:
        return None

    yf = energia_ac_kwh / P_NOMINAL_KWP
    yr = insolacao_kwh_m2 / (G_STC_W_M2 / 1000)
    pr = yf / yr if yr > 0 else None

    return {
        "energia_ac_kwh": round(energia_ac_kwh, 2),
        "insolacao_kwh_m2": round(insolacao_kwh_m2, 3),
        "yf_kwh_por_kwp": round(yf, 3),
        "yr_horas_sol_pleno": round(yr, 3),
        "pr": round(pr, 4) if pr is not None else None,
        "p_nominal_kwp_usado": P_NOMINAL_KWP,
        "registros_usados": len(df),
    }
