from pymongo import MongoClient
from neo4j import GraphDatabase

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

def consulta1_jogos_mais_lucro():
    """
        1. Quais jogos mais dão lucro para a BET?
    """
    pass

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



resultado = consulta2_top_influencers()
