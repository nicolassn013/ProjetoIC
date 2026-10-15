"""
dashboard.py - Passo 6: camada de apresentação sobre o leituras.db.

Este arquivo só LÊ o banco (via consultas.py) e desenha a interface. Toda a
lógica de query fica em consultas.py, e o cálculo de PR fica isolado em
performance_ratio.py -- de propósito, pra não virar um arquivo gigante com
tudo misturado.

Rodar com:  streamlit run dashboard.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import banco
import consultas
import performance_ratio as pr

st.set_page_config(page_title="Monitoramento IFES Serra", layout="wide")

INVERSORES = ["INV01", "INV02", "INV03", "INV04"]
CORES_INVERSORES = {
    "INV01": "#1f77b4",
    "INV02": "#2ca02c",
    "INV03": "#d62728",  # vermelho de propósito - é o inversor do achado
    "INV04": "#9467bd",
}


# ------------------------------------------------------------------
# Conexão e dados base (com cache, pra não reabrir o banco a cada clique)
# ------------------------------------------------------------------

@st.cache_data(ttl=300)
def carregar_dados():
    with banco.conectar() as conn:
        return {
            "datas": consultas.datas_disponiveis(conn),
            "resumo": consultas.resumo_diario(conn),
            "hist_inv": consultas.historico_anual_inversores(conn),
            "hist_inv_long": consultas.historico_anual_inversores_long(conn),
            "hist_usina": consultas.historico_anual_usina(conn),
            "cobertura": consultas.cobertura_geral(conn),
        }


@st.cache_data(ttl=300)
def carregar_dia(data_iso):
    with banco.conectar() as conn:
        return consultas.leitura_15min_do_dia(conn, data_iso)


try:
    dados = carregar_dados()
except banco.BancoNaoEncontrado as erro:
    st.error(str(erro))
    st.stop()

if not dados["datas"]:
    st.warning("O banco existe mas está vazio (nenhum dia em leitura_15min). "
               "Rode o pipeline (pipeline/integra_usina_meteorologia.py) e depois "
               "pipeline/carrega_banco.py antes de usar o dashboard.")
    st.stop()


# ------------------------------------------------------------------
# Navegação
# ------------------------------------------------------------------

pagina = st.sidebar.radio(
    "Seção",
    [
        "Visão geral",
        "Geração da usina",
        "Comparação entre inversores",
        "Histórico 2020–2026",
        "Qualidade dos dados",
        "Meteorologia × Geração",
        "Alertas e diagnóstico",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Usina FV de 119 kW AC / 140 kWp — IFES Campus Serra. "
    "Dados de 2 dias de exemplo (22/09/2025 e 22/09/2026); mais dias entram "
    "automaticamente assim que novos relatórios forem processados pelo "
    "pipeline."
)


# ------------------------------------------------------------------
# 1. Visão geral
# ------------------------------------------------------------------

if pagina == "Visão geral":
    st.title("Visão geral — Usina Fotovoltaica IFES Campus Serra")

    cobertura = dados["cobertura"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dias na base", len(dados["datas"]))
    col2.metric("Registros de 15min", cobertura["total_registros_15min"])
    col3.metric("Com meteorologia", f'{cobertura["pct_meteorologia"]}%')
    col4.metric("Com os 4 inversores", f'{cobertura["pct_4_inversores"]}%')

    if cobertura["timestamps_duplicados"] > 0:
        st.error(f'{cobertura["timestamps_duplicados"]} timestamp(s) duplicado(s) '
                  f'encontrados no banco — isso não deveria acontecer, verificar o pipeline.')
    else:
        st.success("Nenhum timestamp duplicado no banco (checado a cada carregamento).")

    st.subheader("Resumo por dia processado")
    st.dataframe(dados["resumo"], use_container_width=True)

    st.caption(
        "Esta tabela vem direto da tabela `resumo_diario`, gerada pelo Passo 4 "
        "(um registro por dia processado pelo pipeline)."
    )


# ------------------------------------------------------------------
# 2. Geração da usina
# ------------------------------------------------------------------

elif pagina == "Geração da usina":
    st.title("Geração da usina — potência ao longo do dia")

    data_escolhida = st.selectbox("Escolha o dia", dados["datas"])
    df_dia = carregar_dia(data_escolhida)

    if df_dia.empty:
        st.warning("Não há dados de 15min para esse dia.")
    else:
        series_disponiveis = st.multiselect(
            "Séries a mostrar",
            ["Usina (potência total)"] + INVERSORES,
            default=["Usina (potência total)"] + INVERSORES,
        )

        fig = go.Figure()
        if "Usina (potência total)" in series_disponiveis:
            fig.add_trace(go.Scatter(
                x=df_dia["timestamp_15min"], y=df_dia["potencia_fv_kw"],
                name="Usina (medida)", mode="lines", line=dict(width=3, color="black"),
            ))
        for inv in INVERSORES:
            if inv in series_disponiveis:
                fig.add_trace(go.Scatter(
                    x=df_dia["timestamp_15min"], y=df_dia[inv],
                    name=inv, mode="lines", line=dict(color=CORES_INVERSORES[inv]),
                ))
        fig.update_layout(
            xaxis_title="Horário", yaxis_title="Potência (kW)",
            legend_title="Série", height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Usina medida × soma dos inversores")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_dia["timestamp_15min"], y=df_dia["potencia_fv_kw"],
            name="Usina (medida)", mode="lines",
        ))
        fig2.add_trace(go.Scatter(
            x=df_dia["timestamp_15min"], y=df_dia["potencia_inversores_soma_kw"],
            name="Soma dos 4 inversores", mode="lines", line=dict(dash="dash"),
        ))
        fig2.update_layout(xaxis_title="Horário", yaxis_title="Potência (kW)", height=400)
        st.plotly_chart(fig2, use_container_width=True)

        with banco.conectar() as conn:
            resumo_dia = consultas.resumo_do_dia(conn, data_escolhida)
        if resumo_dia is not None and pd.notna(resumo_dia["correlacao_usina_vs_soma_inversores"]):
            st.metric(
                "Correlação usina × soma dos inversores neste dia",
                f'{resumo_dia["correlacao_usina_vs_soma_inversores"]:.6f}',
            )
        st.caption(
            "As duas curvas quase se sobrepõem quando os 4 inversores têm dado "
            "no mesmo instante — é a validação cruzada feita no Passo 3/4."
        )


# ------------------------------------------------------------------
# 3. Comparação entre inversores
# ------------------------------------------------------------------

elif pagina == "Comparação entre inversores":
    st.title("Comparação entre inversores")

    data_escolhida = st.selectbox("Dia de referência", dados["datas"], key="cmp_dia")
    df_dia = carregar_dia(data_escolhida)

    if not df_dia.empty:
        maximos = {inv: df_dia[inv].max() for inv in INVERSORES}
        cols = st.columns(4)
        for col, inv in zip(cols, INVERSORES):
            valor = maximos[inv]
            texto = f"{valor:.2f} kW" if pd.notna(valor) else "sem dado"
            col.metric(f"Pico {inv}", texto)

        st.info(
            "⚠️ **INV03** aparece com valores bem mais baixos de geração histórica "
            "(veja a seção Histórico 2020–2026) — não é erro de leitura deste dia, "
            "é um padrão que se repete ano após ano."
        )

    st.subheader("Participação na geração anual (2026, ano em curso)")
    df_hist = dados["hist_inv"]
    if not df_hist.empty and "2026" in df_hist.columns:
        fig = px.pie(
            df_hist, names="inversor", values="2026",
            color="inversor", color_discrete_map=CORES_INVERSORES,
            title="Participação de cada inversor na geração de 2026 (parcial)",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "2026 é um ano ainda em curso no momento da extração dos dados "
            "(o relatório 'estatístico ALL' cobre até a data em que foi baixado) "
            "— os valores não representam o ano fechado."
        )


# ------------------------------------------------------------------
# 4. Histórico 2020–2026
# ------------------------------------------------------------------

elif pagina == "Histórico 2020–2026":
    st.title("Histórico de geração anual (2020–2026)")

    df_long = dados["hist_inv_long"]
    if df_long.empty:
        st.warning("Sem dados de histórico anual no banco.")
    else:
        fig = px.bar(
            df_long, x="ano", y="geracao_kwh", color="inversor", barmode="group",
            color_discrete_map=CORES_INVERSORES,
            labels={"geracao_kwh": "Geração (kWh)", "ano": "Ano"},
            title="Geração anual por inversor",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.error(
            "**INV03 — achado de diagnóstico:** geração igual a 0 kWh entre 2020 "
            "e 2024 (5 anos seguidos), voltando a gerar em 2025. A causa não foi "
            "determinada a partir dos dados analisados até aqui — fica registrado "
            "como algo a confirmar com quem opera a usina, não como falha do pipeline."
        )

        st.subheader("Tabela completa")
        st.dataframe(dados["hist_inv"], use_container_width=True)
        st.dataframe(dados["hist_usina"], use_container_width=True)


# ------------------------------------------------------------------
# 5. Qualidade dos dados
# ------------------------------------------------------------------

elif pagina == "Qualidade dos dados":
    st.title("Qualidade e cobertura dos dados")

    cobertura = dados["cobertura"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Registros de 15min", cobertura["total_registros_15min"])
    col2.metric("Com meteorologia", f'{cobertura["com_meteorologia"]} ({cobertura["pct_meteorologia"]}%)')
    col3.metric("Com 4 inversores", f'{cobertura["com_4_inversores"]} ({cobertura["pct_4_inversores"]}%)')

    st.subheader("Correlação usina × soma dos inversores, por dia")
    st.dataframe(
        dados["resumo"][["data", "correlacao_usina_vs_soma_inversores",
                          "registros_com_meteorologia", "registros_15min"]],
        use_container_width=True,
    )

    st.subheader("Timestamps duplicados")
    if cobertura["timestamps_duplicados"] == 0:
        st.success("0 timestamps duplicados em `leitura_15min` (testado a cada carregamento do dashboard).")
    else:
        st.error(f'{cobertura["timestamps_duplicados"]} timestamps duplicados encontrados.')

    st.caption(
        "Esta página existe porque o diferencial do projeto não é só mostrar "
        "geração — é mostrar o quanto se pode confiar no dado que está sendo mostrado."
    )


# ------------------------------------------------------------------
# 6. Meteorologia × Geração
# ------------------------------------------------------------------

elif pagina == "Meteorologia × Geração":
    st.title("Meteorologia × Geração")

    data_escolhida = st.selectbox("Dia", dados["datas"], key="meteo_dia")
    df_dia = carregar_dia(data_escolhida)

    if df_dia.empty or not df_dia["meteorologia_disponivel"].any():
        st.warning(
            f"Não há dados meteorológicos disponíveis para {data_escolhida} na base atual "
            "(o arquivo tratado da MAWS55 cobre até 31/07/2026)."
        )
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_dia["timestamp_15min"], y=df_dia["ghi_lppyra02_w_m2"],
            name="Irradiância LPPYRA02 (W/m²)", yaxis="y1",
        ))
        fig.add_trace(go.Scatter(
            x=df_dia["timestamp_15min"], y=df_dia["ghi_lpnet14_w_m2"],
            name="Irradiância LPNET14 (W/m²)", yaxis="y1",
        ))
        fig.add_trace(go.Scatter(
            x=df_dia["timestamp_15min"], y=df_dia["potencia_fv_kw"],
            name="Potência da usina (kW)", yaxis="y2", line=dict(color="black"),
        ))
        fig.update_layout(
            xaxis_title="Horário",
            yaxis=dict(title="Irradiância (W/m²)"),
            yaxis2=dict(title="Potência (kW)", overlaying="y", side="right"),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Performance Ratio (PR)")
        resultado_pr = pr.calcular_pr(df_dia)
        if resultado_pr is None:
            st.warning(
                "PR não calculado para este dia: nem todos os registros de 15min "
                "têm irradiância disponível (o cálculo exige cobertura completa "
                "pra não distorcer o resultado)."
            )
        else:
            colp1, colp2, colp3 = st.columns(3)
            colp1.metric("PR do dia", resultado_pr["pr"])
            colp2.metric("Energia gerada (kWh)", resultado_pr["energia_ac_kwh"])
            colp3.metric("Horas de sol pleno (Yr)", resultado_pr["yr_horas_sol_pleno"])
            with st.expander("Como esse PR foi calculado (fórmula e premissas)"):
                st.markdown(f"""
- **Fórmula (IEC 61724):** `PR = Yf / Yr`, onde `Yf = Energia_AC / P_nominal` e
  `Yr = Insolação (kWh/m²) / 1 kW/m²`.
- **P_nominal usado:** {resultado_pr['p_nominal_kwp_usado']} kWp (potência DC
  nominal dos módulos — não confundir com os 119 kW AC, que é o limite de
  saída dos inversores).
- **Irradiância:** média entre os dois sensores da MAWS55 (LPPYRA02 e
  LPNET14), por não ter informação de calibração de qual é mais confiável.
- **Registros usados:** {resultado_pr['registros_usados']} de 96 possíveis
  (só calculamos quando 100% dos intervalos do dia têm irradiância).
- **Limitação:** PR de 1 dia é sensível a nuvens passageiras e não substitui
  uma análise de período mais longo (mês/ano).
""")


# ------------------------------------------------------------------
# 7. Alertas e diagnóstico
# ------------------------------------------------------------------

elif pagina == "Alertas e diagnóstico":
    st.title("Alertas e diagnóstico")

    st.error(
        "**INV03 — geração zero por 5 anos.** Histórico indica geração igual "
        "a 0 kWh entre 2020 e 2024. Causa não determinada pelos dados "
        "analisados — a confirmar com os responsáveis pela operação da usina."
    )

    st.warning(
        "**INV04 — potência nominal assumida.** A análise usa 14 kW como "
        "potência nominal do INV04 (os outros três são 35 kW cada). Esse "
        "valor ainda depende de confirmação documental — a evidência a favor "
        "é que 35+35+35+14 = 119 kW, batendo exatamente com a potência AC "
        "total da usina, mas isso não é uma prova definitiva."
    )

    st.warning(
        "**Cobertura meteorológica.** O arquivo tratado da MAWS55 cobre até "
        "31/07/2026. Qualquer data posterior fica sem irradiância/temperatura "
        "na base atual, e o dashboard não tenta preencher isso artificialmente."
    )

    st.info(
        "**Strings desconectadas (INV01).** As entradas PV-2, PV-5, PV-8 e "
        "PV-11 do INV01 aparecem com corrente 0,00 A de forma consistente — "
        "interpretado como entrada sem string física conectada, não como falha."
    )

    st.info(
        "**Espaço Energia (KSTAR, 3 kWp).** Ainda não tem um histórico em "
        "lote integrado ao banco como a usina principal — só telemetria "
        "pontual foi inspecionada até agora."
    )

    st.caption(
        "Esta página reúne, num só lugar, os achados de diagnóstico dos "
        "Passos 2 a 5. Nenhum deles foi inventado ou assumido sem evidência "
        "nos dados reais processados pelo pipeline."
    )
