import streamlit as st
import pandas as pd
from utils import supabase, get_parametros, calcular_custo_unitario, calcular_preco_venda_estimado, logo

st.set_page_config(layout="wide")
parametros = get_parametros()

a, b, c = st.columns([2, 1, 2])
with b:
    st.image(logo, width=400)

st.subheader("⚙️ Parâmetros (editar / adicionar)")

with st.expander("✏️ Renomear Tipos de Peça", expanded=False):
    st.markdown("Como os tipos de peças são gerados com base nos produtos atuais, utilize esta ferramenta para **substituir um nome em todos os produtos** (ex: Corrigir erro de digitação).")

    tipos_usados = parametros["tipos_peca"]
    
    colA, colB = st.columns(2)
    with colA:
        antigo = st.selectbox("Valor atual", options=tipos_usados, key="ren_antigo")
    with colB:
        novo = st.text_input("Novo valor", key="ren_novo")
        
    if st.button("✅ Renomear em toda a base", type="primary"):
        if antigo and novo and antigo != novo:
            # Faz o update diretamente na tabela de produtos
            supabase.table("produtos").update({"tipo_peca": novo}).eq("tipo_peca", antigo).execute()
            st.success(f'✅ "{antigo}" → "{novo}" aplicado em todos os produtos.')
            st.rerun()
        else:
            st.warning("Preencha corretamente os nomes.")

with st.expander("💸 Parâmetros de custo", expanded=False):
    custos = parametros.get("custos", {})

    argila = st.number_input("Argila (R$/Kg)", min_value=0.0, step=0.1, value=float(custos.get("argila", 7)))
    embalagem = st.number_input("Embalagem (R$)", min_value=0.0, step=0.1, value=float(custos.get("embalagem", 3)))
    queima_biscoito = st.number_input("Queima Biscoito (R$)", min_value=0.0, step=1.0, value=float(custos.get("queima_biscoito", 210)))
    queima_esmalte = st.number_input("Queima Esmalte (R$)", min_value=0.0, step=1.0, value=float(custos.get("queima_esmalte", 420)))

    esmalte = st.number_input("Esmalte (ex.: 0.1 = 10%)", min_value=0.0, step=0.01, value=float(custos.get("esmalte", 0.1)))
    margem = st.number_input("Margem (ex.: 0.3 = 30%)", min_value=0.0, step=0.05, value=float(custos.get("margem", 0.3)))

    st.markdown("**Fator por tamanho**")
    f_dict = custos.get("fator_tamanho", {})
    colA, colB, colC, colD, colE = st.columns(5)
    with colA:
        f_pp = st.number_input("PP", min_value=0.0, step=0.00001, value=float(f_dict.get("PP", 0.05)), format="%.5f")
    with colB:
        f_p = st.number_input("P", min_value=0.0, step=0.00001, value=float(f_dict.get("P", 0.125)), format="%.5f")
    with colC:
        f_m = st.number_input("M", min_value=0.0, step=0.00001, value=float(f_dict.get("M", 0.17)), format="%.5f")
    with colD:
        f_g = st.number_input("G", min_value=0.0, step=0.00001, value=float(f_dict.get("G", 0.25)), format="%.5f")
    with colE:
        f_gg = st.number_input("GG", min_value=0.0, step=0.00001, value=float(f_dict.get("GG", 0.5)), format="%.5f")

    if st.button("💾 Salvar custos", type="primary"):
        # Upsert na tabela de parâmetros (assumindo ID 1 para linha de configuração única)
        supabase.table("parametros").upsert({
            "id": 1, 
            "argila": float(argila),
            "queima_biscoito": float(queima_biscoito),
            "queima_esmalte": float(queima_esmalte),
            "esmalte": float(esmalte),
            "embalagem": float(embalagem),
            "margem": float(margem)
        }).execute()

        # Upsert na tabela fator_tamanho
        fatores_atualizados = {"PP": f_pp, "P": f_p, "M": f_m, "G": f_g, "GG": f_gg}
        for tam, fat in fatores_atualizados.items():
            supabase.table("fator_tamanho").upsert({"tamanho": tam, "fator": float(fat)}).execute()

        st.success("✅ Parâmetros de custo salvos!")
        st.rerun()

with st.expander("📟 Simulador de Preço", expanded=False):
    t = st.selectbox("Tamanho", ["PP", "P", "M", "G", "GG"])
    p = st.number_input("Peso (Kg)", min_value=0.1, step=0.1, value=0.5)

    custo_novo = calcular_custo_unitario(t, p, parametros)
    preco_venda_novo = calcular_preco_venda_estimado(custo_novo, parametros)

    fator = parametros["custos"]["fator_tamanho"].get(t, 0)

    st.markdown("### ✅ Metodologia atual (custo separado da margem)")
    st.code(
        "💸 → custo_unitario = [(peso × Kg argila) + ((queima_biscoito + queima_esmalte)/4 × fator_tamanho)] × (1 + % esmalte) + preço embalagem\n"
        f"💸 → custo_unitario = [({p}Kg × R${argila}) + ((R${queima_biscoito} + R${queima_esmalte})/4 × {fator*100}%)] × (1 + {int(esmalte*100)}%) + R${embalagem} = R$ {custo_novo:.2f}\n\n"
        "🏷 → preço_estimado_venda = custo_unitario × (1 + % margem)\n"
        f"🏷 → preco_estimado_venda = {custo_novo:.2f} × (1 + {int(margem*100)}%) = R$ {preco_venda_novo:.2f}",
        language="text"
    )

    st.success(f"💸 Custo unitário (sem margem): R$ {custo_novo:,.2f}")
    st.info(f"🏷 Preço estimado de venda (com margem): R$ {preco_venda_novo:,.2f}")
