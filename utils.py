from services.supabase_client import supabase

icon = "assets/logo_icon.png"
logo = "assets/logo.png"


# ---------------------------
# PRODUTOS
# ---------------------------
def get_produtos():
    res = supabase.table("estoque_atual").select("*").execute()
    return res.data

def get_entradas():
    res = supabase.table("entradas_estoque").select("*").execute()
    return res.data

def get_vendas():
    res = supabase.table("vendas").select("*").execute()
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

# ---------------------------
# CALCULOS
# ---------------------------

def calcular_custo_unitario(tamanho, peso, parametros):
    """
    Custo real da peça (sem margem).
    Fórmula:
      custo_base = (peso * argila) + ((queima_biscoito + queima_esmalte) * fator_tamanho) + embalagem
      custo = custo_base * (1 + esmalte)
    """
    parametros = supabase.table("parametros").select("*").execute()

    argila = float(custos.get("argila", 0))
    queima_biscoito = float(custos.get("queima_biscoito", 0))
    queima_esmalte = float(custos.get("queima_esmalte", 0))
    esmalte = float(custos.get("esmalte", 0))
    embalagem = float(custos.get("embalagem", 0))
    fator_por_tamanho = custos.get("fator_tamanho", {}) or {}

    # aceita "Pequeno/Médio/Grande" OU "P/M/G/PP"
    mapa = {
        "pequeno": "P",
        "médio": "M",
        "medio": "M",
        "grande": "G",
        "pp": "PP",
        "p": "P",
        "m": "M",
        "g": "G",
    }

    t = str(tamanho or "").strip()
    if t not in fator_por_tamanho:
        t = mapa.get(t.lower(), t)

    fator = float(fator_por_tamanho.get(t, 0))
    peso = float(peso or 0)

    custo_base = ((peso * argila) + ((queima_biscoito + queima_esmalte)/4 * fator)) * (1 + esmalte)
    custo = custo_base + embalagem

    return round(custo, 2)


