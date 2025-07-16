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

def consulta2_top_influencers():
    """
        2. Quais são os usuários que mais receberam dinheiro a partir da perda dos outros?
    """

    cypher = """
        CALL apoc.mongo.find(
            'mongodb://localhost:27017/pmd-2025', 
            { cliente_ganhou: false }, 
            {
                collection: 'apostas',
                projection: {
                    id_pessoa:           1,
                    valor_apostado:      1,
                    cliente_ganhou:      1,
                    tipo_jogo:           1,
                    odd:                 1,
                    porcentagem_vitoria: 1,
                    resultado_real:      1,
                    resultado_apostado:  1
                },
                sort: {}
            }
        ) YIELD value

        WITH 
        toInteger(value.id_pessoa) AS id_pessoa_perdedor,
        value.valor_apostado      AS valor_apostado,
        value.cliente_ganhou      AS cliente_ganhou,
        value.tipo_jogo           AS tipo_jogo,
        value.odd                 AS odd,
        value.porcentagem_vitoria AS porcentagem_vitoria,
        value.resultado_real      AS resultado_real,
        value.resultado_apostado  AS resultado_apostado

        MATCH (perdedor:Usuario { userId: id_pessoa_perdedor })

        OPTIONAL MATCH p=(perdedor)-[*1..]->(beneficiado:Usuario)
        WHERE beneficiado IS NOT NULL

        RETURN
        id_pessoa_perdedor,
        perdedor.nome             AS nome_perdedor,
        valor_apostado,
        cliente_ganhou,
        tipo_jogo,
        odd,
        porcentagem_vitoria,
        resultado_real,
        resultado_apostado,
        collect(DISTINCT beneficiado.nome) AS beneficiado,
        collect(DISTINCT length(p))        AS distancia_ao_beneficiado
        ORDER BY id_pessoa_perdedor
    """

    with neo_driver.session() as session:
        records = session.run(cypher).data()
    neo_driver.close()

    ganhos_por_beneficiado = {}

    for record in records:
        perda = record["valor_apostado"]
        beneficiados = record["beneficiado"]
        distancias = record["distancia_ao_beneficiado"]

        for i in range(len(beneficiados)):
            beneficiado_nome = beneficiados[i]
            distancia = distancias[i]

            if distancia >= 1:
                percentual_ganho = 0.10 * (0.5 ** (distancia - 1))
                ganho = perda * percentual_ganho
                
                ganhos_por_beneficiado[beneficiado_nome] = ganhos_por_beneficiado.get(beneficiado_nome, 0) + ganho
        
    df = pd.DataFrame(list(ganhos_por_beneficiado.items()), columns=['influencer', 'total_gain'])

    df = df.sort_values(by='total_gain', ascending=False)

    if not df.empty:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['influencer'], df['total_gain'])
        plt.xlabel("Influenciador")
        plt.ylabel("Ganhos a partir das perdas (R$)")
        plt.title("Top Usuários por Ganhos de Perdas de Outros")
        plt.xticks(rotation=45, ha='right')

        top_val = df['total_gain'].max()
        for bar in bars:
            h = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                h + top_val * 0.01,
                f"{h:,.2f}",
                ha='center',
                va='bottom',
                fontsize=9
            )

        plt.tight_layout()
        plt.show()

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

def consulta4_mais_trouxe_novos_usuarios():
    """
        Qual usuário conseguiu trazer mais novos usuários diretos?
    """
    cypher = """
    MATCH (u:Usuario)-[:INDICADO_POR]->(influencer:Usuario)
    RETURN influencer.nome AS Usuario, count(u) AS TotalApontamentosDiretos
    ORDER BY TotalApontamentosDiretos DESC
    """

    with neo_driver.session() as session:
        records_apontamentos = session.run(cypher).data()
    neo_driver.close()

    df_apontamentos = pd.DataFrame([
        {"Usuario": record["Usuario"], "TotalApontamentosDiretos": record["TotalApontamentosDiretos"]}
        for record in records_apontamentos
    ])

    df_top_10 = df_apontamentos.head(10)

    plt.figure(figsize=(12, 7))
    bars = plt.bar(df_top_10['Usuario'], df_top_10['TotalApontamentosDiretos'], color='skyblue')
    
    plt.xlabel("Usuário", fontsize=12)
    plt.ylabel("Número de Apontamentos Diretos", fontsize=12)
    plt.title("Top 10 Usuários por Novos Apontamentos Diretos", fontsize=14)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(df_top_10['TotalApontamentosDiretos']) * 0.01,
            f"{int(height)}",
            ha='center',
            va='bottom',
            fontsize=9
        )

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

def consulta6_porcentagem_vitoria_cada_jogo():
    """
    Qual a porcentagem de vitória para cada jogo?
    """
    pipeline = [
        {
            "$group": {
                "_id": "$tipo_jogo",
                "total_apostas": {"$sum": 1},
                "total_vitorias": {
                    "$sum": {
                    "$cond": [
                        {"$eq": ["$cliente_ganhou", True]},
                        1,
                        0 
                    ]
                }
                }, 
            }
        },
        {
            "$sort": {"porcentagem_vitoria": -1}
        }
    ]

    data = list(coll.aggregate(pipeline))

    df = pd.DataFrame(data)

    df['porcentagem_vitoria'] = df['total_vitorias'] / df['total_apostas']

    plt.figure(figsize=(10, 6))
    bars = plt.bar(df['_id'], df['porcentagem_vitoria'], color='lightgreen')
    
    plt.xlabel("Tipo de Jogo", fontsize=12)
    plt.ylabel("Porcentagem de Vitória (%)", fontsize=12)
    plt.title("Porcentagem de Vitórias por Tipo de Jogo", fontsize=14)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(df['porcentagem_vitoria']) * 0.01,
            f"{height:.2f}%",
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.tight_layout()
    plt.show()

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

def consulta8_quanto_influencer_ganhou(nome_influenciador="Sophia Ramos"):
    """
    Quanto um usuário específico já ganhou por conta de perdas de usuários que usam seu cupom?
    """

    cypher = """
        CALL apoc.mongo.find(
            'mongodb://localhost:27017/pmd-2025', 
            { cliente_ganhou: false }, 
            {
                collection: 'apostas',
                projection: {
                    id_pessoa:           1,
                    valor_apostado:      1,
                    cliente_ganhou:      1,
                    tipo_jogo:           1,
                    odd:                 1,
                    porcentagem_vitoria: 1,
                    resultado_real:      1,
                    resultado_apostado:  1
                },
                sort: {}
            }
        ) YIELD value

        WITH 
        toInteger(value.id_pessoa) AS id_pessoa_perdedor,
        value.valor_apostado      AS valor_apostado,
        value.cliente_ganhou      AS cliente_ganhou,
        value.tipo_jogo           AS tipo_jogo,
        value.odd                 AS odd,
        value.porcentagem_vitoria AS porcentagem_vitoria,
        value.resultado_real      AS resultado_real,
        value.resultado_apostado  AS resultado_apostado

        MATCH (perdedor:Usuario { userId: id_pessoa_perdedor })

        OPTIONAL MATCH p=(perdedor)-[*1..]->(beneficiado:Usuario{nome: $nome})
        WHERE beneficiado IS NOT NULL

        RETURN
        id_pessoa_perdedor,
        perdedor.nome             AS nome_perdedor,
        valor_apostado,
        cliente_ganhou,
        tipo_jogo,
        odd,
        porcentagem_vitoria,
        resultado_real,
        resultado_apostado,
        collect(DISTINCT beneficiado.nome) AS beneficiado,
        collect(DISTINCT length(p))        AS distancia_ao_beneficiado
        ORDER BY id_pessoa_perdedor
    """

    with neo_driver.session() as session:
        records = session.run(cypher, nome=nome_influenciador).data()
    neo_driver.close()

    ganhos_por_beneficiado = {}

    for record in records:
        perda = record["valor_apostado"]
        beneficiados = record["beneficiado"]
        distancias = record["distancia_ao_beneficiado"]

        for i in range(len(beneficiados)):
            beneficiado_nome = beneficiados[i]
            distancia = distancias[i]

            if distancia >= 1:
                percentual_ganho = 0.10 * (0.5 ** (distancia - 1))
                ganho = perda * percentual_ganho
                
                ganhos_por_beneficiado[beneficiado_nome] = ganhos_por_beneficiado.get(beneficiado_nome, 0) + ganho
        
    df = pd.DataFrame(list(ganhos_por_beneficiado.items()), columns=['influencer', 'total_gain'])

    df = df.sort_values(by='total_gain', ascending=False)

    if not df.empty:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['influencer'], df['total_gain'])
        plt.xlabel("Influenciador")
        plt.ylabel("Ganhos a partir das perdas (R$)")
        plt.title("Top Usuários por Ganhos de Perdas de Outros")
        plt.xticks(rotation=45, ha='right')

        top_val = df['total_gain'].max()
        for bar in bars:
            h = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                h + top_val * 0.01,
                f"{h:,.2f}",
                ha='center',
                va='bottom',
                fontsize=9
            )

        plt.tight_layout()
        plt.show()

def exibir_menu():
    print("\n" + "="*40)
    print("        Menu de Consultas de Apostas       ")
    print("="*40)
    print("1. Quais jogos mais dão lucro para a BET?")
    print("2. Quais são os usuários que mais receberam dinheiro a partir da perda dos outros?")
    print("3. Quais são os usuários que mais receberam dinheiro somente a partir de apostas?")
    print("4. Qual usuário conseguiu trazer mais novos usuários diretos?")
    print("5. Qual a porcentagem de usuários que utilizam código?")
    print("6. Qual a porcentagem de vitória para cada jogo?")
    print("7. Qual usuário conseguiu trazer mais novos usuários diretos e indiretos?")
    print("8. Quanto um usuário específico já ganhou por conta de perdas de usuários que usam seu cupom?")
    print("0. Sair")
    print("="*40)

while True:
    exibir_menu()
    escolha = int(input("Digite o número da consulta desejada: "))
    
    if escolha == 1:
        consulta1_jogos_mais_lucro()
    elif escolha == 2:
        consulta2_top_influencers()
    elif escolha == 3:
        coonsulta3_top_apostadores()
    elif escolha == 4:
        consulta4_mais_trouxe_novos_usuarios()
    elif escolha == 5:
        consulta5_quantos_usuarios_usam_codigo()
    elif escolha == 6:
        consulta6_porcentagem_vitoria_cada_jogo()
    elif escolha == 7:
        consulta7_quem_mais_indicou()
    elif escolha == 8:
        consulta8_quanto_influencer_ganhou()
    elif escolha == 0:
        print("Saindo do programa. Até mais!")
        break
    else:
        print("Opção inválida. Por favor, digite um número entre 0 e 8.")
