from services.supabase_client import supabase

icon = "logo_icon.png"
logo = "logo.png"


# ---------------------------
# PRODUTOS
# ---------------------------
def get_produtos():
    res = supabase.table("produtos").select("*").execute()
    return res.data


def criar_produto(produto: dict):
    return supabase.table("produtos").insert(produto).execute()


def atualizar_produto(produto_id, dados):
    return supabase.table("produtos").update(dados).eq("id", produto_id).execute()


# ---------------------------
# ESTOQUE
# ---------------------------
def registrar_entrada(produto_id, quantidade, tipo="producao", obs=""):
    data = {
        "produto_id": produto_id,
        "quantidade": quantidade,
        "tipo": tipo,
        "observacao": obs,
    }
    return supabase.table("entradas_estoque").insert(data).execute()


# ---------------------------
# VENDAS
# ---------------------------
def registrar_venda(produto_id, quantidade, preco_unitario, custo_unitario):
    data = {
        "produto_id": produto_id,
        "quantidade": quantidade,
        "preco_unitario_vendido": preco_unitario,
        "custo_unitario_snapshot": custo_unitario,
        "valor_total": preco_unitario * quantidade,
    }
    return supabase.table("vendas").insert(data).execute()
