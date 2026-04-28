import streamlit as st
import pandas as pd
from datetime import date
from utils import get_produtos, get_vendas, insert_venda, icon


st.set_page_config(layout="wide")


produtos = get_produtos()
vendas = get_vendas()


# recalcular estoque (simples em memória)
df_p = pd.DataFrame(produtos)
df_v = pd.DataFrame(vendas)

if not df_p.empty:
    vend = df_v.groupby("produto_id")["quantidade"].sum() if not df_v.empty else 0
    df_p["estoque_atual"] = df_p["id"].map(vend).fillna(0).rsub(df_p.get("estoque_atual", 0))

# HEADER
a, b = st.columns([1, 10])

with a:
    st.image(icon, width=100)

with b:
    st.title("💰 Vendas e Indicadores")


disponiveis = df_p[df_p.get("estoque_atual", 0) > 0].to_dict("records")

col1, col2 = st.columns([1, 2])


# ---------------------------
# NOVA VENDA
# ---------------------------
with col1:
    st.subheader("💵 Nova venda")

    if not disponiveis:
        st.info("Sem estoque.")
    else:
        prod = st.selectbox(
            "Produto",
            disponiveis,
            format_func=lambda p: f'{p["id"]} — {p["nome"]}'
        )

        with st.form("venda"):
            qtd = st.number_input("Quantidade", 1, int(prod["estoque_atual"]), 1)
            preco = st.number_input("Preço unitário", 0.0, step=10.0)
            data = st.date_input("Data", value=date.today())
            obs = st.text_input("Obs")

            ok = st.form_submit_button("Registrar", type="primary")

        if ok:
            insert_venda({
                "produto_id": prod["id"],
                "quantidade": int(qtd),
                "preco_unitario_vendido": float(preco),
                "valor_total": float(preco * qtd),
                "data_venda": data.strftime("%Y-%m-%d"),
                "observacao": obs
            })

            st.success("Venda registrada")
            st.rerun()


# ---------------------------
# TABELA
# ---------------------------
with col2:
    st.subheader("📋 Vendas")

    if df_v.empty:
        st.info("Sem vendas")
    else:
        df_show = df_v.merge(
            df_p[["id", "nome"]],
            left_on="produto_id",
            right_on="id",
            how="left"
        )

        st.dataframe(df_show, use_container_width=True)


# ---------------------------
# INDICADORES
# ---------------------------
st.divider()
st.subheader("📊 Indicadores")

if not df_v.empty:
    total = df_v["valor_total"].sum()
    qtd = df_v["quantidade"].sum()

    st.metric("Total vendido", f"R$ {total:,.2f}")
    st.metric("Peças vendidas", int(qtd))