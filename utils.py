import streamlit as st
from supabase import create_client, Client

logo = "assets/logo.png"
icon = "assets/logo_icon.png"

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def get_next_id(tabela: str, id_col: str = "id") -> int:
    """Busca o maior ID da tabela e retorna o próximo válido."""
    res = supabase.table(tabela).select(id_col).order(id_col, desc=True).limit(1).execute()
    if res.data:
        return int(res.data[0][id_col]) + 1
    return 1

def get_parametros() -> dict:
    """Busca os parâmetros de custos e fatores do banco de dados."""
    try:
        res_p = supabase.table("parametros").select("*").limit(1).execute()
        p_data = res_p.data[0] if res_p.data else {}
    except Exception:
        p_data = {}

    try:
        res_f = supabase.table("fator_tamanho").select("*").execute()
        f_data = {item["tamanho"]: float(item["fator"]) for item in res_f.data} if res_f.data else {}
    except Exception:
        f_data = {}

    # Extrai tipos_peca de forma dinâmica dos produtos (pois não há tabela específica no schema)
    try:
        res_t = supabase.table("produtos").select("tipo_peca").execute()
        tipos_peca = sorted(list(set(item["tipo_peca"] for item in res_t.data if item.get("tipo_peca"))))
    except Exception:
        tipos_peca = []

    return {
        "tipos_peca": tipos_peca,
        "tamanho_peca": list(f_data.keys()) if f_data else ["PP", "P", "M", "G", "GG"],
        "custos": {
            "argila": float(p_data.get("argila", 0)),
            "queima_biscoito": float(p_data.get("queima_biscoito", 0)),
            "queima_esmalte": float(p_data.get("queima_esmalte", 0)),
            "esmalte": float(p_data.get("esmalte", 0)),
            "embalagem": float(p_data.get("embalagem", 0)),
            "margem": float(p_data.get("margem", 0)),
            "fator_tamanho": f_data,
        }
    }

def get_produtos_com_estoque() -> list:
    """Busca os produtos e calcula o estoque dinamicamente baseando nas movimentações."""
    produtos = supabase.table("produtos").select("*").execute().data or []
    entradas = supabase.table("entradas_estoque").select("produto_id, quantidade").execute().data or []
    vendas = supabase.table("vendas").select("produto_id, quantidade").execute().data or []

    estoque = {}
    for e in entradas:
        pid = e["produto_id"]
        estoque[pid] = estoque.get(pid, 0) + (e["quantidade"] or 0)
    
    for v in vendas:
        pid = v["produto_id"]
        estoque[pid] = estoque.get(pid, 0) - (v["quantidade"] or 0)

    for p in produtos:
        p["estoque_atual"] = estoque.get(p["id"], 0)
    
    return produtos

def calcular_custo_unitario(tamanho, peso, parametros):
    custos = parametros.get("custos", {})
    argila = float(custos.get("argila", 0))
    queima_biscoito = float(custos.get("queima_biscoito", 0))
    queima_esmalte = float(custos.get("queima_esmalte", 0))
    esmalte = float(custos.get("esmalte", 0))
    embalagem = float(custos.get("embalagem", 0))
    
    fator_por_tamanho = custos.get("fator_tamanho", {})
    
    mapa = {"pequeno": "P", "médio": "M", "medio": "M", "grande": "G", "pp": "PP", "p": "P", "m": "M", "g": "G"}
    t = str(tamanho or "").strip()
    if t not in fator_por_tamanho:
        t = mapa.get(t.lower(), t)
        
    fator = float(fator_por_tamanho.get(t, 0))
    peso = float(peso or 0)

    custo_base = ((peso * argila) + ((queima_biscoito + queima_esmalte)/4 * fator)) * (1 + esmalte)
    custo = custo_base + embalagem
    return round(custo, 2)

def calcular_preco_venda_estimado(custo_unitario, parametros):
    margem = float(parametros.get("custos", {}).get("margem", 0))
    return round(float(custo_unitario or 0) * (1 + margem), 2)
