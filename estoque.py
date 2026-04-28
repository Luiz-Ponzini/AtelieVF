import streamlit as st
import pandas as pd
from utils import icon
from services.supabase_client import supabase

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(layout="wide")

# ---------------------------
# DADOS (SUPABASE)
# ---------------------------
produtos = supabase.schema("public").table("produtos").select("*").execute().data
entradas = supabase.table("entradas_estoque").select("*").execute().data
vendas = supabase.table("vendas").select("*").execute().data

dfp = pd.DataFrame(produtos)

if dfp.empty:
    st.info("Nenhum produto cadastrado ainda.")
    st.stop()

# ---------------------------
# HEADER
# ---------------------------
a, b = st.columns([1, 10])

with a:
    st.image(icon, width=100)

with b:
    st.title("📦 Estoque")

# ---------------------------
# ESTOQUE (já vem da VIEW)
# ---------------------------
if "estoque" in dfp.columns:
    dfp["estoque_atual"] = dfp["estoque"].fillna(0).astype(int)
else:
    dfp["estoque_atual"] = 0

# ---------------------------
# FILTROS
# ---------------------------
st.markdown("### 🔎 Filtros")

c1, c2, c3 = st.columns(3)

tipos_op = sorted(dfp["tipo_peca"].dropna().unique().tolist()) if "tipo_peca" in dfp else []
tamanhos_op = sorted(dfp["tamanho"].dropna().unique().tolist()) if "tamanho" in dfp else []

with c1:
    busca = st.text_input("Buscar por nome")

with c2:
    f_tipos = st.multiselect("Tipo", options=tipos_op)

with c3:
    f_tamanhos = st.multiselect("Tamanho", options=tamanhos_op)

mostrar_zero = st.checkbox("Mostrar produtos com estoque 0", value=True)

# ---------------------------
# FILTRO LÓGICO
# ---------------------------
f = dfp.copy()

if busca:
    f = f[f["nome"].str.lower().str.contains(busca.lower(), na=False)]

if f_tipos:
    f = f[f["tipo_peca"].isin(f_tipos)]

if f_tamanhos:
    f = f[f["tamanho"].isin(f_tamanhos)]

if not mostrar_zero:
    f = f[f["estoque_atual"] > 0]

# ---------------------------
# TABELA PRINCIPAL
# ---------------------------
st.markdown("### 📋 Produtos (estoque atual)")

st.dataframe(
    f.sort_values(["estoque_atual", "nome"], ascending=[False, True]),
    use_container_width=True
)

st.divider()

# ---------------------------
# MOVIMENTAÇÕES
# ---------------------------
st.markdown("### 🧾 Movimentações (últimas)")

colA, colB = st.columns(2)

dfp_nome = dfp[["id", "nome"]].rename(
    columns={"id": "produto_id", "nome": "produto_nome"}
)

# ---------------------------
# ENTRADAS
# ---------------------------
with colA:
    st.subheader("➕ Entradas (produção)")

    dfe = pd.DataFrame(entradas)

    if not dfe.empty:
        dfe = dfe.merge(dfp_nome, on="produto_id", how="left")

        cols = ["id", "produto_nome", "data", "quantidade", "tipo", "observacao"]
        dfe = dfe[[c for c in cols if c in dfe.columns]]

        dfe["data"] = pd.to_datetime(dfe["data"], errors="coerce")

        st.dataframe(
            dfe.sort_values("data", ascending=False).head(30),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sem entradas.")

# ---------------------------
# VENDAS
# ---------------------------
with colB:
    st.subheader("➖ Vendas")

    dfv = pd.DataFrame(vendas)

    if not dfv.empty:
        dfv = dfv.merge(dfp_nome, on="produto_id", how="left")

        cols = [
            "data_venda",
            "produto_nome",
            "quantidade",
            "preco_unitario_vendido",
            "custo_unitario_snapshot",
            "valor_total",
            "observacao"
        ]

        dfv = dfv[[c for c in cols if c in dfv.columns]]

        dfv["data_venda"] = pd.to_datetime(dfv["data_venda"], errors="coerce")

        st.dataframe(
            dfv.sort_values("data_venda", ascending=False).head(30),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sem vendas.")
