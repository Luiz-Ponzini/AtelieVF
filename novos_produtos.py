import streamlit as st
import pandas as pd
from datetime import date
from utils import (
    supabase, get_parametros, get_produtos_com_estoque, get_next_id,
    calcular_custo_unitario, calcular_preco_venda_estimado, logo
)

st.set_page_config(layout="wide")
parametros = get_parametros()
produtos = get_produtos_com_estoque()

tipos_peca = parametros["tipos_peca"] or ["Prato", "Tigela", "Copo", "Vaso"] # Fallback se base vazia
tamanho_peca = parametros["tamanho_peca"]

a, b, c = st.columns([2, 1, 2])
with b:
    st.image(logo, width=400)

col1, col2 = st.columns(2)

with col1:
    st.title("📝 Cadastro de Produtos + Produção")

    with st.expander("➕ Abrir formulário de cadastro", expanded=False):
        nome = st.text_input("Nome do produto (ex.: Prato Azul Gaia)")
        tipo = st.selectbox("Tipo da peça", options=tipos_peca + ["Criar novo tipo..."])
        if tipo == "Criar novo tipo...":
            tipo = st.text_input("Digite o novo tipo")
            
        tamanho = st.selectbox("Tamanho", options=tamanho_peca)
        peso = st.number_input("Peso unitário (Kg)", min_value=0.001, step=0.001, value=0.5, format="%.3f")

        custo_calc = calcular_custo_unitario(tamanho, peso, parametros)
        preco_venda_calc = calcular_preco_venda_estimado(custo_calc, parametros)
        data_producao = st.date_input("Data da produção", value=date.today())
        quantidade_inicial = st.number_input("Quantidade produzida agora (entrada inicial)", min_value=0, step=1, value=0)

        col11, col12 = st.columns(2)
        with col11:
            st.metric("Custo unitário (calculado, sem margem)", f"R$ {custo_calc:.2f}")
        with col12:
            st.metric("Preço estimado de venda (com margem)", f"R$ {preco_venda_calc:.2f}")

        enviar = st.button("Adicionar produto", type='primary')

        if enviar:
            pid = get_next_id("produtos")
            novo_prod = {
                "id": pid,
                "nome": nome.strip() or f"Produto {pid}",
                "tipo_peca": tipo,
                "tamanho": tamanho,
                "peso_kg_unitario": float(peso),
                "custo_unitario": float(custo_calc),
                "preco_venda_estimado": float(preco_venda_calc),
                "ativo": True,
                "data_cadastro": data_producao.strftime("%Y-%m-%d")
            }
            supabase.table("produtos").insert(novo_prod).execute()

            if quantidade_inicial > 0:
                eid = get_next_id("entradas_estoque")
                nova_entrada = {
                    "id": eid,
                    "produto_id": pid,
                    "data": data_producao.strftime("%Y-%m-%d"),
                    "quantidade": int(quantidade_inicial),
                    "tipo": "producao",
                    "observacao": "Entrada inicial no cadastro"
                }
                supabase.table("entradas_estoque").insert(nova_entrada).execute()

            st.success("✅ Produto cadastrado! Estoque atualizado.")
            st.rerun()

    if not produtos:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        with st.expander("✏️ Editar dados do produto", expanded=False):
            prod_sel = st.selectbox(
                "Selecione o produto",
                options=produtos,
                format_func=lambda p: f'{p["id"]} — {p.get("nome","")} (Estoque: {p.get("estoque_atual",0)})',
                key="select_produto_edicao"
            )
            pid = prod_sel["id"]

            nome_e = st.text_input("Nome", value=prod_sel.get("nome", ""), key=f"nome_{pid}")
            tipo_e = st.selectbox("Tipo da peça", options=tipos_peca + ["Criar novo tipo..."], 
                                  index=tipos_peca.index(prod_sel.get("tipo_peca")) if prod_sel.get("tipo_peca") in tipos_peca else 0, key=f"tipo_{pid}")
            if tipo_e == "Criar novo tipo...":
                tipo_e = st.text_input("Digite o novo tipo", key=f"tipo_novo_{pid}")

            tamanho_e = st.selectbox("Tamanho", options=tamanho_peca, 
                                     index=tamanho_peca.index(prod_sel.get("tamanho")) if prod_sel.get("tamanho") in tamanho_peca else 0, key=f"tamanho_{pid}")

            peso_e = st.number_input("Peso unitário (Kg)", min_value=0.001, step=0.001, format="%.3f", value=float(prod_sel.get("peso_kg_unitario", 0.5)), key=f"peso_{pid}")

            custo_calc2 = calcular_custo_unitario(tamanho_e, peso_e, parametros)
            preco_venda_calc2 = calcular_preco_venda_estimado(custo_calc2, parametros)

            col11, col12 = st.columns(2)
            with col11:
                st.metric("Custo unitário (calculado, sem margem)", f"R$ {custo_calc2:.2f}")
            with col12:
                st.metric("Preço estimado de venda (com margem)", f"R$ {preco_venda_calc2:.2f}")

            ativo_e = st.checkbox("Ativo", value=bool(prod_sel.get("ativo", True)), key=f"ativo_{pid}")
            salvar_btn = st.button("Salvar alterações", type="primary", key=f"salvar_{pid}")

            if salvar_btn:
                supabase.table("produtos").update({
                    "nome": nome_e.strip() or prod_sel["nome"],
                    "tipo_peca": tipo_e,
                    "tamanho": tamanho_e,
                    "peso_kg_unitario": float(peso_e),
                    "custo_unitario": float(custo_calc2),
                    "preco_venda_estimado": float(preco_venda_calc2),
                    "ativo": bool(ativo_e)
                }).eq("id", pid).execute()
                
                st.success("✅ Produto atualizado!")
                st.rerun()

        with st.expander("📦 Adicionar produção (entrada de estoque)", expanded=False):
            prod = st.selectbox(
                "Selecione o produto",
                options=produtos,
                format_func=lambda p: f'{p["id"]} — {p.get("nome","")} (Estoque: {p.get("estoque_atual",0)})',
                key="select_produto_estoque"
            )
            pid_estoque = prod["id"]
            qtd = st.number_input("Quantidade produzida", min_value=1, step=1, value=1)
            dt = st.date_input("Data da produção", value=date.today(), key="data_producao_add_producao")
            obs = st.text_input("Observação (opcional)")
            add = st.button("Registrar entrada")

            if add:
                eid = get_next_id("entradas_estoque")
                nova_entrada = {
                    "id": eid,
                    "produto_id": pid_estoque,
                    "data": dt.strftime("%Y-%m-%d"),
                    "quantidade": int(qtd),
                    "tipo": "producao",
                    "observacao": obs.strip()
                }
                supabase.table("entradas_estoque").insert(nova_entrada).execute()
                st.success("✅ Entrada registrada! Estoque atualizado.")
                st.rerun()

with col2:
    st.title("📋 Produtos cadastrados")
    if produtos:
        df = pd.DataFrame(produtos)
        colunas = ["nome", "tipo_peca", "tamanho", "peso_kg_unitario", "custo_unitario", "preco_venda_estimado", "estoque_atual", "ativo"]
        st.dataframe(df[colunas], width="stretch", height = "stretch", hide_index=True)
    else:
        st.info("Nenhum produto cadastrado.")
