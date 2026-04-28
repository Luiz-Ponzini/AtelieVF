import streamlit as st

novos_produtos_page = st.Page("novos_produtos.py", title="Adicionar/Editar Produto", icon="📝")
estoque_page = st.Page("estoque.py", title="Estoque", icon="📦")
parametros_page = st.Page("parametros.py", title="Parametros", icon="⚙️")
financeiro_page = st.Page("financeiro.py", title="Financeiro", icon="💵")

#pg = st.navigation([estoque_page, novos_produtos_page, financeiro_page, parametros_page],position="top")
st.set_page_config(page_title="Ateliê Vera Figueiredo", page_icon="🏺")
#pg.run()

st.logo(
    image="assets/logo.png", size="large",
    icon_image="assets/logo_icon.png"  # opcional
)

pg = st.navigation(
        [estoque_page, novos_produtos_page, financeiro_page, parametros_page],
        position="sidebar",   # 👈 aqui
        expanded=True,
    )
pg.run()