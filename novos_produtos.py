import streamlit as st
import pandas as pd
from datetime import date

from utils import (
    get_produtos,
    insert_produto,
    update_produto,
    insert_entrada,
    get_entradas,
    recalcular_estoque,
    calcular_custo_unitario,
    calcular_preco_venda_estimado,
    icon
)

st.set_page_config(layout="wide")


# ---------------------------
# DATA
# ---------------------------
produtos = get_produtos()
entradas = get_entradas()

df_prod = pd.DataFrame(produtos)


# recalcula estoque em memória
if not df_prod.empty:
    df_ent = pd.DataFrame(entradas)

    if not df_ent.empty:
        ent = df_ent.groupby("produto_id")["quantidade"].sum()
    else:
        ent = pd.Series(dtype=int)

    df_prod["estoque_atual"] = df_prod["id"].map(ent).fillna(0).astype(int)


# ---------------------------
# HEADER
# ---------------------------
a, b, c = st.columns([2, 1, 2])

with b:
    st.image(icon, width=400)


col1, col2 = st.columns(2)


# =========================================================
# COLUNA 1 — CADASTRO
# =========================================================
with col1:
    st.title("📝 Cadastro de Produtos + Produção")

    with st.expander("➕ Abrir formulário de cadastro"):

        nome = st.text_input("Nome do produto")
        tipo = st.text_input("Tipo da peça")
        tamanho = st.text_input("Tamanho")

        peso = st.number_input(
            "Peso unitário (Kg)",
            min_value=0.1,
            step=0.001,
            value=0.5,
            format="%.3f"
        )

        data_producao = st.date_input("Data da produção", value=date.today())

        qtd_inicial = st.number_input("Quantidade inicial", min_value=0, step=1)

        # cálculo ao vivo
        custo_calc = calcular_custo_unitario(tamanho, peso, {})
        preco_calc = calcular_preco_venda_estimado(custo_calc, {})

        col11, col12 = st.columns(2)
        with col11:
            st.metric("Custo unitário", f"R$ {custo_calc:.2f}")
        with col12:
            st.metric("Preço estimado", f"R$ {preco_calc:.2f}")

        if st.button("Adicionar produto", type="primary"):

            novo = {
                "nome": nome,
                "tipo_peca": tipo,
                "tamanho": tamanho,
                "peso_kg_unitario": float(peso),
                "custo_unitario": float(custo_calc),
                "preco_venda_estimado": float(preco_calc),
                "ativo": True
            }

            resp = insert_produto(novo)
            prod_id = resp.data[0]["id"]

            # entrada inicial
            if qtd_inicial > 0:
                insert_entrada({
                    "produto_id": prod_id,
                    "quantidade": int(qtd_inicial),
                    "data": data_producao.strftime("%Y-%m-%d"),
                    "tipo": "producao",
                    "observacao": "Entrada inicial"
                })

            st.success("Produto criado!")
            st.rerun()


    # =========================================================
    # EDIÇÃO
    # =========================================================
    st.divider()
    st.subheader("✏️ Editar produto")

    if df_prod.empty:
        st.info("Sem produtos")
    else:

        prod = st.selectbox(
            "Produto",
            df_prod.to_dict("records"),
            format_func=lambda p: f'{p["id"]} — {p["nome"]}'
        )

        nome_e = st.text_input("Nome", prod["nome"])
        tipo_e = st.text_input("Tipo", prod.get("tipo_peca", ""))
        tamanho_e = st.text_input("Tamanho", prod.get("tamanho", ""))
        peso_e = st.number_input(
            "Peso",
            value=float(prod.get("peso_kg_unitario", 0.5)),
            step=0.001,
            format="%.3f"
        )

        custo_calc2 = calcular_custo_unitario(tamanho_e, peso_e, {})
        preco_calc2 = calcular_preco_venda_estimado(custo_calc2, {})

        col11, col12 = st.columns(2)
        with col11:
            st.metric("Custo", f"R$ {custo_calc2:.2f}")
        with col12:
            st.metric("Preço", f"R$ {preco_calc2:.2f}")

        ativo = st.checkbox("Ativo", value=prod.get("ativo", True))

        if st.button("Salvar alterações", type="primary"):

            update_produto(prod["id"], {
                "nome": nome_e,
                "tipo_peca": tipo_e,
                "tamanho": tamanho_e,
                "peso_kg_unitario": float(peso_e),
                "custo_unitario": float(custo_calc2),
                "preco_venda_estimado": float(preco_calc2),
                "ativo": ativo
            })

            st.success("Atualizado!")
            st.rerun()


# =========================================================
# COLUNA 2 — LISTAGEM
# =========================================================
with col2:
    st.title("📋 Produtos")

    if df_prod.empty:
        st.info("Sem produtos")
    else:
        st.dataframe(
            df_prod[
                [
                    "id", "nome", "tipo_peca", "tamanho",
                    "peso_kg_unitario", "custo_unitario",
                    "preco_venda_estimado", "estoque_atual", "ativo"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )