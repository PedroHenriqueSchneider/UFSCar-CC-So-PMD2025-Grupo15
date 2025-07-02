import pandas as pd
import numpy as np
from faker import Faker
import random
import uuid
import os
from datetime import datetime

print("Iniciando a geração de dados para a BET...")

NUM_TOTAL_USUARIOS = 20 
NUM_INFLUENCIADORES_RAIZ = 5  
PERCENTUAL_SEM_INDICACAO = 0.15 

CIDADES_COMUNS = [
    'São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza',
    'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Goiânia'
]

fake = Faker('pt_BR')

def gerar_codigo_indicacao(nome):
    """Gera um código de indicação a partir do nome do usuário."""
    nome_sem_espaco = nome.split(' ')[0].lower()
    numero_aleatorio = random.randint(100, 999)
    return f"{nome_sem_espaco}{numero_aleatorio}"

def criar_diretorio_saida(nome_dir='neo4j_import_data'):
    """Cria o diretório para salvar os arquivos CSV se não existir."""
    if not os.path.exists(nome_dir):
        os.makedirs(nome_dir)
        print(f"Diretório '{nome_dir}' criado.")
    return nome_dir

print(f"Gerando {NUM_TOTAL_USUARIOS} usuários...")

usuarios_lista = []
indicacoes_lista = []
usuarios_sem_indicacao = int(NUM_TOTAL_USUARIOS * PERCENTUAL_SEM_INDICACAO)
usuarios_com_indicacao = NUM_TOTAL_USUARIOS - usuarios_sem_indicacao

for i in range(NUM_INFLUENCIADORES_RAIZ + usuarios_sem_indicacao):
    nome = fake.name()
    usuarios_lista.append({
        'userId': str(uuid.uuid4()),
        'nome': nome,
        'cidade': random.choice(CIDADES_COMUNS),
        'data_cadastro': fake.iso8601(),
        'codigo_indicacao': gerar_codigo_indicacao(nome),
        'indicado_por_id': None # Não foram indicados
    })

for i in range(usuarios_com_indicacao):
    indicador = random.choice(usuarios_lista)
    
    nome = fake.name()
    novo_usuario = {
        'userId': str(uuid.uuid4()),
        'nome': nome,
        'cidade': random.choice(CIDADES_COMUNS),
        'data_cadastro': fake.iso8601(),
        'codigo_indicacao': gerar_codigo_indicacao(nome),
        'indicado_por_id': indicador['userId']
    }
    usuarios_lista.append(novo_usuario)

    indicacoes_lista.append({
        'start_userId': novo_usuario['userId'], 
        'end_userId': indicador['userId'] 
    })

usuarios_df = pd.DataFrame(usuarios_lista)
indicacoes_df = pd.DataFrame(indicacoes_lista)
print(f"{len(usuarios_df)} usuários e {len(indicacoes_df)} relações de indicação geradas.")

print("Simulando histórico de apostas para cada usuário...")

apostas_lista = []
rel_fez_aposta_lista = []

print("Preparando arquivos CSV para importação no Neo4j...")
output_dir = criar_diretorio_saida()

usuarios_nodes = pd.DataFrame({
    'userId:ID(User)': usuarios_df['userId'],
    'nome:string': usuarios_df['nome'],
    'cidade:string': usuarios_df['cidade'],
    'dataCadastro:datetime': usuarios_df['data_cadastro'],
    'codigoIndicacao:string': usuarios_df['codigo_indicacao'],
    ':LABEL': 'Usuario'
})
usuarios_nodes.to_csv(os.path.join(output_dir, 'usuarios.csv'), index=False)
pd.DataFrame(usuarios_nodes.columns).T.to_csv(os.path.join(output_dir, 'usuarios_header.csv'), index=False, header=False)

rel_indicacoes = pd.DataFrame({
    ':START_ID(User)': indicacoes_df['start_userId'],
    ':END_ID(User)': indicacoes_df['end_userId'],
    ':TYPE': 'INDICADO_POR'
})
rel_indicacoes.to_csv(os.path.join(output_dir, 'rel_indicacoes.csv'), index=False)
pd.DataFrame(rel_indicacoes.columns).T.to_csv(os.path.join(output_dir, 'rel_indicacoes_header.csv'), index=False, header=False)

print("\nConcluído!")
print(f"Arquivos gerados no diretório: '{output_dir}'")
print("\nPRÓXIMO PASSO: Importar os dados para o Neo4j.")

# Código Cypher para importação no Neo4j
cypher_code = '''
// 1. Cria os nós de usuários
LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
CREATE (:Usuario {
  userId: row.`userId:ID(User)`,
  nome: row.`nome:string`,
  cidade: row.`cidade:string`,
  dataCadastro: row.`dataCadastro:datetime`,
  codigoIndicacao: row.`codigoIndicacao:string`
});

// 2. Cria as relações de indicação entre os usuários
LOAD CSV WITH HEADERS FROM 'file:///rel_indicacoes.csv' AS row
MATCH (u1:Usuario {userId: row.`:START_ID(User)`})
MATCH (u2:Usuario {userId: row.`:END_ID(User)`})
CREATE (u1)-[:INDICADO_POR]->(u2);
'''

# Salva o código Cypher em um arquivo separado
cypher_file_path = os.path.join(output_dir, 'import_cypher.txt')
with open(cypher_file_path, 'w', encoding='utf-8') as f:
    f.write(cypher_code)

print(f"\nCódigo Cypher salvo em: '{cypher_file_path}'")
print("\nPara importar no Neo4j:")
print("1. Copie os arquivos usuarios.csv e rel_indicacoes.csv para a pasta /import do Neo4j")
print("2. Execute o código Cypher acima no Neo4j Browser ou cypher-shell")
