import streamlit as st
import pandas as pd
from datetime import date
from utils import supabase, get_produtos_com_estoque, get_next_id, icon

st.set_page_config(layout="wide")
produtos = get_produtos_com_estoque()
vendas = supabase.table("vendas").select("*").execute().data or []

a, b = st.columns([1, 10])
with a:
    st.image(icon, width=100)
with b:
    st.title("💰 Vendas e Indicadores")

# só produtos com estoque > 0 e ativos
disponiveis = [p for p in produtos if p.get("ativo", True) and int(p.get("estoque_atual", 0)) > 0]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("💵 Nova venda")
    if not disponiveis:
        st.info("Nenhum produto disponível em estoque para venda.")
    else:
        prod = st.selectbox(
            "Produto",
            options=disponiveis,
            format_func=lambda p: f'{p["id"]} — {p["nome"]} (Estoque: {p["estoque_atual"]})'
        )

        estoque_max = int(prod.get("estoque_atual", 0))
        custo_unit = float(prod.get("custo_unitario", 0) or 0)
        preco_est_venda = float(prod.get("preco_venda_estimado", 0) or 0)

        with st.form("form_venda"):
            st.number_input("Custo unitário (referência)", value=custo_unit, disabled=True)
            st.number_input("Preço estimado de venda (referência)", value=preco_est_venda, disabled=True)

            quantidade = st.number_input("Quantidade vendida", min_value=1, max_value=max(1, estoque_max), step=1, value=1)
            preco_unit = st.number_input("Preço unitário vendido (R$)", min_value=0.0, step=10.0, value=0.0)
            data_venda = st.date_input("Data da venda", value=date.today())
            obs = st.text_input("Observação (opcional)")

            vender = st.form_submit_button("Registrar venda", type="primary")

        if vender:
            if int(quantidade) > estoque_max:
                st.error(f"Estoque insuficiente. Disponível: {estoque_max}")
            else:
                vid = get_next_id("vendas")
                valor_total = round(float(preco_unit) * int(quantidade), 2)

                nova_venda = {
                    "id": vid,
                    "produto_id": prod["id"],
                    "data_venda": data_venda.strftime("%Y-%m-%d"),
                    "quantidade": int(quantidade),
                    "preco_unitario_vendido": float(preco_unit),
                    "custo_unitario_snapshot": custo_unit,
                    "valor_total": float(valor_total),
                    "observacao": obs.strip()
                }

                supabase.table("vendas").insert(nova_venda).execute()
                st.success("✅ Venda registrada! Estoque atualizado.")
                st.rerun()

with col2:
    if not vendas:
        st.info("Ainda não há vendas registradas.")
    else:
        dfv = pd.DataFrame(vendas)
        dfp = pd.DataFrame(produtos)[["id", "nome"]].rename(
            columns={"id": "produto_id", "nome": "produto_nome"}
        )

        dfv = dfv.merge(dfp, on="produto_id", how="left")
        col_order = ["data_venda", "produto_nome", "quantidade", "preco_unitario_vendido", "custo_unitario_snapshot", "valor_total", "observacao"]
        col_order = [c for c in col_order if c in dfv.columns]
        dfv = dfv[col_order]

        st.subheader("🧾 Tabela de vendas")
        st.dataframe(dfv.sort_values("data_venda", ascending=False), width="stretch", height=665, hide_index=True)

st.divider()
st.subheader("📊 Indicadores")

if not vendas:
    st.info("Ainda não há vendas registradas.")
else:
    dfv["quantidade"] = dfv.get("quantidade", 1).fillna(0).astype(int)
    
    if "valor_total" not in dfv.columns:
        if "preco_unitario_vendido" in dfv.columns:
            dfv["valor_total"] = dfv["preco_unitario_vendido"].fillna(0).astype(float) * dfv["quantidade"]
        else:
            dfv["valor_total"] = 0.0
    dfv["valor_total"] = dfv["valor_total"].fillna(0).astype(float)
    dfv["custo_unitario_snapshot"] = dfv.get("custo_unitario_snapshot", 0).fillna(0).astype(float)
    dfv["data_venda"] = pd.to_datetime(dfv.get("data_venda"), errors="coerce")

    total_vendido = float(dfv["valor_total"].sum())
    custo_total = float((dfv["custo_unitario_snapshot"] * dfv["quantidade"]).sum())
    lucro_total = round(total_vendido - custo_total, 2)
    pecas_vendidas = int(dfv["quantidade"].sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total vendido", f"R$ {total_vendido:,.2f}")
    c2.metric("Lucro (venda − custo)", f"R$ {lucro_total:,.2f}")
    c3.metric("Peças vendidas", f"{pecas_vendidas}")

    df_month = dfv.dropna(subset=["data_venda"]).copy()
    if not df_month.empty:
        df_group = df_month.groupby(df_month["data_venda"].dt.to_period("M"))["valor_total"].sum()
        df_group.index = df_group.index.to_timestamp()
        st.subheader("📈 Vendas por mês")
        st.line_chart(df_group)
