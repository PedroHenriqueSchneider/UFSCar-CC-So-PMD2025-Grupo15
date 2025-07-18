import random
import os
from datetime import datetime
from faker import Faker
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth
from collections import defaultdict

load_dotenv()

NUM_TOTAL_USUARIOS = 50
NUM_INFLUENCIADORES_RAIZ = 5

NUM_TOTAL_USUARIOS -= NUM_INFLUENCIADORES_RAIZ # Um influenciador também é um usuário

PERCENTUAL_SEM_INDICACAO = 0.15
CIDADES_COMUNS = [
    'São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza',
    'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Goiânia'
]

fake = Faker('pt_BR')

def gerar_codigo_indicacao(nome):
    nome_sem_espaco = nome.split(' ')[0].lower()
    numero_aleatorio = random.randint(100, 999)
    return f"{nome_sem_espaco}{numero_aleatorio}"

# Inicializa driver
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASS")))

id_usuario = 0
def get_id():
    global id_usuario
    id_usuario += 1
    return id_usuario
    
def creates_cycle(child_id, parent_id, edges):
    adj = defaultdict(list)
    for c, p in edges:
        adj[c].append(p)

    stack = [parent_id]
    visited = set()
    while stack:
        node = stack.pop()
        if node == child_id:
            return True
        for nxt in adj.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return False

with driver.session() as session:
    # Limpando dados antigos (opcional)
    session.run("MATCH (u:Usuario) DETACH DELETE u")

    usuarios = []
    indicacoes = []
    usuarios_sem_ind = int(NUM_TOTAL_USUARIOS * PERCENTUAL_SEM_INDICACAO)
    usuarios_com_ind = NUM_TOTAL_USUARIOS - usuarios_sem_ind

    # Cria influenciadores raiz e usuários sem indicação
    for _ in range(NUM_INFLUENCIADORES_RAIZ + usuarios_sem_ind):
        nome = fake.name()
        usuario = {
            'userId': get_id(),
            'nome': nome,
            'cidade': random.choice(CIDADES_COMUNS),
            'dataCadastro': fake.iso8601(),
            'codigoIndicacao': gerar_codigo_indicacao(nome),
            'indicadoPor': None
        }
        usuarios.append(usuario)

    # Cria usuários com indicação
    for _ in range(usuarios_com_ind):
        indicador = random.choice(usuarios)
        nome = fake.name()
        usuario = {
            'userId': get_id(),
            'nome': nome,
            'cidade': random.choice(CIDADES_COMUNS),
            'dataCadastro': fake.iso8601(),
            'codigoIndicacao': gerar_codigo_indicacao(nome),
            'indicadoPor': indicador['userId']
        }
        while creates_cycle(usuario['userId'], indicador['userId'], indicacoes):
            indicador = random.choice(usuarios)
        usuarios.append(usuario)
        indicacoes.append((usuario['userId'], indicador['userId']))

    # Insere nós Usuario
    print(f"Criando {len(usuarios)} nós de Usuario...")
    tx = session.begin_transaction()
    for u in usuarios:
        tx.run(
            """
            CREATE (u:Usuario {
                userId: $userId,
                nome: $nome,
                cidade: $cidade,
                dataCadastro: datetime($dataCadastro),
                codigoIndicacao: $codigoIndicacao
            })
            """,
            userId=u['userId'],
            nome=u['nome'],
            cidade=u['cidade'],
            dataCadastro=u['dataCadastro'],
            codigoIndicacao=u['codigoIndicacao']
        )
    tx.commit()

    # Insere relações INDICADO_POR
    print(f"Criando {len(indicacoes)} relações INDICADO_POR...")
    tx = session.begin_transaction()
    for child_id, parent_id in indicacoes:
        tx.run(
            """
            MATCH (c:Usuario {userId: $child}), (p:Usuario {userId: $parent})
            CREATE (c)-[:INDICADO_POR]->(p)
            """,
            child=child_id,
            parent=parent_id
        )
    tx.commit()

print("Importação concluída no Neo4j.")
driver.close()
