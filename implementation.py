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
NEO4J_DB   = 'pmd'    

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
    cypher = """
        CALL apoc.mongo.find(
        'mongodb://localhost:27017/pmd-2025', 
        {}, 
        {
            collection: 'apostas',
            projection: {
            id_pessoa:            1,
            valor_apostado:       1,
            cliente_ganhou:       1,
            tipo_jogo:            1,
            odd:                  1,
            porcentagem_vitoria:  1,
            resultado_real:       1,
            resultado_apostado:   1
            },
            sort: {}
        }
        ) YIELD value

        WITH 
        toInteger(value.id_pessoa) AS id_pessoa,
        value.valor_apostado       AS valor_apostado,
        value.cliente_ganhou       AS cliente_ganhou,
        value.tipo_jogo            AS tipo_jogo,
        value.odd                  AS odd,
        value.porcentagem_vitoria  AS porcentagem_vitoria,
        value.resultado_real       AS resultado_real,
        value.resultado_apostado   AS resultado_apostado

        MATCH (u:Usuario { userId: id_pessoa })
        RETURN
        id_pessoa,
        u.nome                     AS nome,
        valor_apostado,
        cliente_ganhou,
        tipo_jogo,
        odd,
        porcentagem_vitoria,
        resultado_real,
        resultado_apostado;
    """
    with neo_driver.session() as session:
        records = session.run(cypher).data()
    neo_driver.close()

    df = pd.DataFrame(records)

    df['lucro'] = df.apply(calcular_lucro, axis=1)
    df['recebido'] = df['lucro'].apply(lambda x: -x)

    receb_por_usuario = df.groupby('nome')['recebido'] \
                        .sum() \
                        .sort_values(ascending=False)

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

    cypher = """
    CALL apoc.mongo.find(
      'mongodb://localhost:27017/pmd-2025',
      {},
      {
        collection: 'apostas',
        projection: { id_pessoa: 1 },
        sort: {}
      }
    ) YIELD value
    WITH collect(DISTINCT toInteger(value.id_pessoa)) AS bettors

    WITH size(bettors) AS total_bettors

    MATCH (u:Usuario)-[:INDICADO_POR]->()
    WITH total_bettors, count(DISTINCT u.userId) AS usaram_codigo

    RETURN
      CASE 
        WHEN total_bettors = 0 THEN 0.0 
        ELSE toFloat(usaram_codigo) / total_bettors * 100 
      END AS porcentagem
    """

    with neo_driver.session() as session:
        porcentagem = session.run(cypher).single()["porcentagem"]
    neo_driver.close()

    print(f"Porcentagem de usuários que utilizaram código: {porcentagem:.2f}%")

# consulta = int(input("Qual consulta você deseja realizar? "))

def consulta7_quem_mais_indicou():
    """
    Qual usuário conseguiu trazer mais novos usuários diretos e indiretos?
    """
    cypher = """
    MATCH (u:Usuario)
    OPTIONAL MATCH (ref:Usuario)-[:INDICADO_POR*1..]->(u)
    WITH u, COUNT(DISTINCT ref) AS total_indicacoes
    RETURN 
      u.nome              AS nome, 
      total_indicacoes
    ORDER BY total_indicacoes DESC
    LIMIT 10
    """
    with neo_driver.session() as session:
        result = session.run(cypher)
        dados = [(record["nome"], record["total_indicacoes"]) 
                 for record in result]
    neo_driver.close()

    if not dados:
        print("Nenhum dado retornado.")
        return

    nomes, contagens = zip(*dados)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(nomes, contagens)
    plt.xlabel("Nome do Usuário")
    plt.ylabel("Quantidade de Indicações")
    plt.title("Usuários por Indicações Diretas e Indiretas")
    plt.xticks(rotation=45, ha="right")

    # Adiciona o valor acima de cada barra
    max_val = max(contagens)
    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            h + max_val * 0.01,
            f"{h}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.tight_layout()
    plt.show()

def consulta9_quanto_influencer_ganhou(nome_influenciador="Samuel Machado"):
    """
    Quanto um usuário específico já ganhou por conta de perdas de usuários que usam seu cupom?
    """

    cypher = """
    MATCH (inf:Usuario { nome: $nome })
    MATCH (u:Usuario)
    WITH shortestPath((inf)<-[:INDICADO_POR*1..]-(u)) as path
    WITH u.nome as nome
    WITH length(path) AS lvl
    WITH reduce(co = 0.1, i IN range(2, lvl) | co * 0.5) AS coef
    CALL apoc.mongo.find(
      'mongodb://localhost:27017/pmd-2025',
      { id_pessoa: toString(u.userId) },
      {
        collection: 'apostas',
        projection: {
          id_pessoa: 1,
          valor_apostado: 1,
          cliente_ganhou: 1,
          tipo_jogo: 1,
          odd: 1,
          porcentagem_vitoria: 1,
          resultado_real: 1,
          resultado_apostado: 1
        },
        sort: {}
      }
    ) YIELD value
    RETURN
      nome                          AS indicado,
      coef                            AS coeficiente,
      value.valor_apostado            AS valor_apostado,
      value.cliente_ganhou            AS cliente_ganhou,
      value.tipo_jogo                 AS tipo_jogo,
      (value.odd * coef)              AS odd,
      value.porcentagem_vitoria       AS porcentagem_vitoria,
      value.resultado_real            AS resultado_real,
      value.resultado_apostado        AS resultado_apostado
    """
    with neo_driver.session() as session:
        records = session.run(cypher, nome=nome_influenciador).data()
    neo_driver.close()

    df = pd.DataFrame(records)
    if df.empty:
        print("Nenhuma aposta encontrada para indicação de", nome_influenciador)
        return

    df['lucro'] = df.apply(calcular_lucro, axis=1)

    total_lucro = df['lucro'].sum()
    print(f"Total de lucro para {nome_influenciador}: R$ {total_lucro:,.2f}")

    lucro_por_indicado = df.groupby('indicado')['lucro'] \
                           .sum() \
                           .sort_values(ascending=False)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(lucro_por_indicado.index, lucro_por_indicado.values)
    plt.xlabel("Usuário Indicado")
    plt.ylabel("Lucro (R$)")
    plt.title(f"Lucro por Indicações de {nome_influenciador}")
    plt.xticks(rotation=45, ha="right")

    max_val = lucro_por_indicado.max()
    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            h + max_val * 0.01,
            f"{h:,.2f}",
            ha="center", va="bottom", fontsize=9
        )

    plt.tight_layout()
    plt.show()

consulta = 9

if consulta == 1:
    consulta1_jogos_mais_lucro()
elif consulta == 3:
    coonsulta3_top_apostadores()
elif consulta == 5:
    consulta5_quantos_usuarios_usam_codigo()
elif consulta == 7:
    consulta7_quem_mais_indicou()
elif consulta == 9:
    consulta9_quanto_influencer_ganhou()