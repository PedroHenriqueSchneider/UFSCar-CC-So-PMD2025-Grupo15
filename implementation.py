from pymongo import MongoClient
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import pandas as pd

# --- Configurações de conexão ---
MONGO_URI    = 'mongodb://localhost:27017'
MONGO_DB     = 'pmd-2025'
MONGO_COLL   = 'apostas'

NEO4J_URI    = 'neo4j://127.0.0.1:7687'
NEO4J_USER   = 'neo4j'
NEO4J_PASS   = '12345678'
NEO4J_DB   = 'mitinho'    

mongo_client = MongoClient(MONGO_URI)
db           = mongo_client[MONGO_DB]
coll         = db[MONGO_COLL]

neo_driver   = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# utils
def calcular_lucro(row):
    v = row['valor_apostado']
    tipo = row['tipo_jogo']
    if tipo != 'caça-níquel' and row['cliente_ganhou'] == False:
        return v

    if tipo == 'aposta esportiva':
        if row['resultado_real'] == row['resultado_apostado']:
            valor_ganho = v * 1.2
        else:
            valor_ganho = row['odd'] * v

    elif tipo == 'caça-níquel':
        p = row.get('porcentagem_vitoria', 0)
        if p == 1:
            valor_ganho = v * 4
        elif p == 0.8:
            valor_ganho = v * 2
        elif p == 0.6:
            valor_ganho = 0
        else:
            return v # derrota

    else:
        valor_ganho = row['odd'] * v

    return - valor_ganho


def consulta1_jogos_mais_lucro():
    """
        1. Quais jogos mais dão lucro para a BET?
    """
    cursor = coll.find(
    {},
        {
            "valor_apostado": 1,
            "cliente_ganhou": 1,
            "tipo_jogo": 1,
            "odd": 1,
            "porcentagem_vitoria": 1,
            "resultado_real": 1,
            "resultado_apostado": 1,
        }
    )

    df = pd.DataFrame(list(cursor))

    df['lucro'] = df.apply(calcular_lucro, axis=1)
    lucro_por_jogo = (
        df.groupby('tipo_jogo')['lucro']
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    bars = plt.bar(lucro_por_jogo.index, lucro_por_jogo.values)

    for bar in bars:
        altura = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2, 
            altura + max(lucro_por_jogo.values) * 0.01,
            f"Lucro TOTAL (R$)\n{altura:,.2f}",  
            ha='center',                        
            va='bottom',                     
            fontsize=9
        )

    plt.ylabel('Lucro Total (R$)')
    plt.xlabel('Tipo de Jogo')
    plt.title('Lucro por Tipo de Jogo (do mais ao menos lucrativo)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def consulta2_top_influencers(limit=10):
    """
        2. Quais são os usuários que mais receberam dinheiro a partir da perda dos outros?
    """
    # 1) Extrai pares (influencer, perdedor, profundidade) do Neo4j
    with neo_driver.session() as session:
        result = session.run("""
            MATCH (ref:User), (los:User)
            WHERE (ref)-[:REFERRED*1..]->(los)
            WITH ref, los, shortestPath((ref)-[:REFERRED*1..]->(los)) AS p
            RETURN ref.id AS influencer_id, los.id AS perdedor_id, length(p) AS profundidade
        """)
        paths = result.values()

    earnings = {}
    for influencer_id, perdedor_id, profundidade in paths:
        pct = 0.1 * (0.5 ** (profundidade - 1))
        # total perdido pelo perdedor
        agg = coll.aggregate([
            { '$match': {
                'id_pessoa': perdedor_id,
                'cliente_ganhou': False
            }},
            { '$group': {
                '_id': None,
                'total_loss': { '$sum': '$valor_apostado' }
            }}
        ])
        total_loss = next(agg, {}).get('total_loss', 0)
        earnings[influencer_id] = earnings.get(influencer_id, 0) + total_loss * pct

    # ordena e retorna top N
    return sorted(
        earnings.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]

def coonsulta3_top_apostadores():
    """
    Quais são os usuários que mais receberam dinheiro somente a partir de apostas?
    """
    docs = list(coll.find({}, {
        "id_pessoa": 1, "valor_apostado": 1, "cliente_ganhou": 1,
        "tipo_jogo": 1, "odd": 1, "porcentagem_vitoria": 1,
        "resultado_real": 1, "resultado_apostado": 1
    }))
    df = pd.DataFrame(docs)

    df['lucro'] = df.apply(calcular_lucro, axis=1)
    df['recebido'] = df['lucro'].apply(lambda x: -x)

    receb_por_usuario = df.groupby('id_pessoa')['recebido'] \
                        .sum() \
                        .sort_values(ascending=False)

    top_ids = receb_por_usuario.index.tolist()
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        res = session.run(
            "MATCH (u:Usuario) RETURN u.userId AS id, u.nome AS nome"
        )
        id_to_nome = {r['id']: r['nome'] for r in res}
    driver.close()

    receb_por_usuario.index = [id_to_nome[int(x)] for x in receb_por_usuario.index]
    top_recebedores = receb_por_usuario[:10]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(top_recebedores.index, top_recebedores.values)

    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            h + top_recebedores.max() * 0.01,
            f"{h:,.2f}",
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.ylabel('Dinheiro Recebido (R$)')
    plt.xlabel('Usuário')
    plt.title('Top Usuários por Dinheiro Recebido em Apostas')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def consulta5_quantos_usuarios_usam_codigo():
    """
    Qual a porcentagem de usuários que utilizam código?
    """

    bettors_ids = coll.distinct("id_pessoa")
    total_bettors = len(bettors_ids)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session() as session:

        q_code = """
        MATCH (u:Usuario)-[:INDICADO_POR]->()
        RETURN count(DISTINCT u) AS usaram_codigo
        """
        usaram_codigo = session.run(q_code).single()["usaram_codigo"]

    driver.close()

    porcentagem = (usaram_codigo / total_bettors) * 100 if total_bettors else 0
    
    print(f"Porcentagem de usuários que utilizaram código: {porcentagem:.2f}%")

# consulta = int(input("Qual consulta você deseja realizar? "))
consulta = 5

if consulta == 1:
    consulta1_jogos_mais_lucro()
elif consulta == 3:
    coonsulta3_top_apostadores()
elif consulta == 5:
    consulta5_quantos_usuarios_usam_codigo()