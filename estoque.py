import streamlit as st
import pandas as pd
from utils import supabase, get_produtos_com_estoque, icon

st.set_page_config(layout="wide")

produtos = get_produtos_com_estoque()
entradas = supabase.table("entradas_estoque").select("*").execute().data or []
vendas = supabase.table("vendas").select("*").execute().data or []

a, b = st.columns([1, 10])
with a:
    st.image(icon, width=100)
with b:
    st.title("📦 Estoque")

dfp = pd.DataFrame(produtos)
if dfp.empty:
    st.info("Nenhum produto cadastrado ainda.")
    st.stop()

dfp["estoque_atual"] = dfp.get("estoque_atual", 0).fillna(0).astype(int)

st.markdown("### 🔎 Filtros")
c1, c2, c3 = st.columns(3)

tipos_op = sorted([x for x in dfp.get("tipo_peca", pd.Series([])).dropna().unique().tolist() if str(x).strip()])
tamanhos_op = sorted([x for x in dfp.get("tamanho", pd.Series([])).dropna().unique().tolist() if str(x).strip()])

with c1:
    busca = st.text_input("Buscar por nome")
with c2:
    f_tipos = st.multiselect("Tipo", options=tipos_op)
with c3:
    f_tamanhos = st.multiselect("Tamanho", options=tamanhos_op)
mostrar_zero = st.checkbox("Mostrar produtos com estoque 0", value=True)

f = dfp.copy()
if busca:
    b = busca.strip().lower()
    f = f[f["nome"].fillna("").str.lower().str.contains(b)]
if f_tipos:
    f = f[f["tipo_peca"].isin(f_tipos)]
if f_tamanhos:
    f = f[f["tamanho"].isin(f_tamanhos)]
if not mostrar_zero:
    f = f[f["estoque_atual"] > 0]

st.markdown("### 📋 Produtos (estoque atual)")
st.dataframe(
    f.sort_values(["estoque_atual", "nome"], ascending=[False, True]), width="stretch"
)

st.divider()
st.markdown("### 🧾 Movimentações (últimas)")

colA, colB = st.columns(2)

dfp_nomes = pd.DataFrame(produtos)[["id", "nome"]].rename(
    columns={"id": "produto_id", "nome": "produto_nome"}
)

with colA:
    st.subheader("➕ Entradas (produção)")
    dfe = pd.DataFrame(entradas)
    if dfe.empty:
        st.info("Sem entradas.")
    else:
        dfe = dfe.merge(dfp_nomes, on="produto_id", how="left")    
        col_order1 = ["id", "produto_nome", "data", "quantidade", "tipo", "observacao"]
        col_order1 = [c for c in col_order1 if c in dfe.columns]
        dfe = dfe[col_order1]  
        dfe["data"] = pd.to_datetime(dfe["data"], errors="coerce")
        st.dataframe(dfe.sort_values("data", ascending=False).head(30), width="stretch", hide_index=True)

with colB:
    st.subheader("➖ Vendas")
    dfv = pd.DataFrame(vendas)
    if dfv.empty:
        st.info("Sem vendas.")
    else:
        dfv = dfv.merge(dfp_nomes, on="produto_id", how="left")    
        col_order = ["data_venda", "produto_nome", "quantidade", "preco_unitario_vendido", "custo_unitario_snapshot", "valor_total", "observacao"]
        col_order = [c for c in col_order if c in dfv.columns]
        dfv = dfv[col_order]    
        dfv["data_venda"] = pd.to_datetime(dfv["data_venda"], errors="coerce")
        st.dataframe(dfv.sort_values("data_venda", ascending=False).head(30), width="stretch", hide_index=True)
