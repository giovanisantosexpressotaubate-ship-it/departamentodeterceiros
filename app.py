import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Departamento de Terceiros",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Departamento de Terceiros - BI Operacional")


# -----------------------------
# CAMINHO DO ARQUIVO
# -----------------------------
ARQUIVO = os.path.join(os.path.dirname(__file__), "dados.xlsx.xlsx")


# -----------------------------
# CARREGAMENTO DE DADOS
# -----------------------------
@st.cache_data(ttl=60)  # atualiza a cada 60s (para “quase tempo real”)
def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return pd.DataFrame()

    df = pd.read_excel(ARQUIVO)
    df.columns = df.columns.str.strip()

    # datas
    df["EMISSÃO"] = pd.to_datetime(df["EMISSÃO"], errors="coerce", dayfirst=True)

    # valores
    df["VALOR"] = (
        df["VALOR"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce")

    return df


df = carregar_dados()

# -----------------------------
# TRATAMENTO DE ERRO (EVITA TELA BRANCA)
# -----------------------------
if df.empty:
    st.warning("⚠️ Nenhum dado encontrado. Verifique se o arquivo 'dados.xlsx' está na pasta do app.")
    st.stop()


# -----------------------------
# FILTROS
# -----------------------------
st.sidebar.header("🔎 Filtros")

motorista = st.sidebar.multiselect("Motorista", df["MOTORISTA"].dropna().unique())
tipo = st.sidebar.multiselect("Tipo", df["TIPO"].dropna().unique())
natureza = st.sidebar.multiselect("Natureza", df["NATUREZA"].dropna().unique())

min_date = df["EMISSÃO"].min()
max_date = df["EMISSÃO"].max()

data_range = st.sidebar.date_input("Período", [min_date, max_date])


# -----------------------------
# FILTRAGEM
# -----------------------------
df_f = df.copy()

if motorista:
    df_f = df_f[df_f["MOTORISTA"].isin(motorista)]

if tipo:
    df_f = df_f[df_f["TIPO"].isin(tipo)]

if natureza:
    df_f = df_f[df_f["NATUREZA"].isin(natureza)]

df_f = df_f[
    (df_f["EMISSÃO"] >= pd.to_datetime(data_range[0])) &
    (df_f["EMISSÃO"] <= pd.to_datetime(data_range[1]))
]


# -----------------------------
# KPIs
# -----------------------------
total = df_f["VALOR"].sum()
debito = df_f[df_f["TIPO"].str.lower() == "débito"]["VALOR"].sum()
credito = df_f[df_f["TIPO"].str.lower() == "crédito"]["VALOR"].sum()

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {total:,.2f}")
c2.metric("📉 Débitos", f"R$ {debito:,.2f}")
c3.metric("📈 Créditos", f"R$ {credito:,.2f}")

st.divider()


# -----------------------------
# GRÁFICOS
# -----------------------------
c4, c5 = st.columns(2)

fig1 = px.bar(
    df_f.groupby("MOTORISTA")["VALOR"].sum().reset_index(),
    x="MOTORISTA",
    y="VALOR",
    title="Valores por Motorista"
)

c4.plotly_chart(fig1, use_container_width=True)


fig2 = px.pie(
    df_f.groupby("TIPO")["VALOR"].sum().reset_index(),
    names="TIPO",
    values="VALOR",
    title="Débito x Crédito"
)

c5.plotly_chart(fig2, use_container_width=True)


st.divider()

# -----------------------------
# TABELA
# -----------------------------
st.subheader("📄 Base de Dados")
st.dataframe(df_f, use_container_width=True)


# -----------------------------
# RANKING
# -----------------------------
st.subheader("🏆 Top Motoristas")

ranking = df_f.groupby("MOTORISTA")["VALOR"].sum().sort_values(ascending=False).head(10)
st.dataframe(ranking)