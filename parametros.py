import streamlit as st
import pandas as pd
from utils import (
    get_produtos,
    atualizar_produto,
    calcular_custo_unitario,
    calcular_preco_venda_estimado,
    logo
)

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(layout="wide")

produtos = get_produtos()

# ---------------------------
# HEADER
# ---------------------------
a, b, c = st.columns([2, 1, 2])
with b:
    st.image(logo, width=400)

st.title("⚙️ Parâmetros e Produtos")

# ---------------------------
# RELOAD AUX
# ---------------------------
def reload_produtos():
    return get_produtos()

# ---------------------------
# LISTA DE TIPOS USADOS
# ---------------------------
tipos_usados = sorted({
    p["tipo_peca"] for p in produtos if p.get("tipo_peca")
})

tamanhos_usados = sorted({
    p["tamanho"] for p in produtos if p.get("tamanho")
})

# ---------------------------
# RENOMEAR GLOBAL (SUPABASE)
# ---------------------------
def renomear_em_produtos(campo, antigo, novo):
    for p in produtos:
        if p.get(campo) == antigo:
            atualizar_produto(p["id"], {campo: novo})

# ---------------------------
# UI
# ---------------------------
st.subheader("🔁 Renomear valores globais")

col1, col2, col3 = st.columns(3)

with col1:
    campo = st.selectbox("Campo", ["tipo_peca", "tamanho"])

with col2:
    if campo == "tipo_peca":
        antigo = st.selectbox("Atual", tipos_usados)
    else:
        antigo = st.selectbox("Atual", tamanhos_usados)

with col3:
    novo = st.text_input("Novo valor")

if st.button("Aplicar renomeação", type="primary"):
    if antigo and novo and antigo != novo:
        renomear_em_produtos(campo, antigo, novo)
        st.success("Atualizado no Supabase!")
        st.rerun()


# ---------------------------
# CUSTOS (AGORA POR PRODUTO OU GLOBAL?)
# ---------------------------
st.divider()
st.subheader("💸 Simulador de custo")

t = st.selectbox("Tamanho", ["PP", "P", "M", "G", "GG"])
p = st.number_input("Peso (kg)", value=0.5)

# ⚠️ aqui você precisa decidir:
# se custos estão em tabela no Supabase OU fixos
# vou assumir que você ainda calcula via função:

# pega qualquer produto só para puxar "referência"
ref_produto = produtos[0] if produtos else None

if ref_produto:
    custo = calcular_custo_unitario(
        t,
        p,
        ref_produto.get("parametros") if ref_produto else {}
    )
    preco = calcular_preco_venda_estimado(
        custo,
        ref_produto.get("parametros") if ref_produto else {}
    )

    st.success(f"Custo unitário: R$ {custo:.2f}")
    st.info(f"Preço estimado: R$ {preco:.2f}")
else:
    st.warning("Sem produtos cadastrados ainda.")