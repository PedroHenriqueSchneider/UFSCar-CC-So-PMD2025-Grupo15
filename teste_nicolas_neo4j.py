from faker import Faker
import random
import uuid
from datetime import date, timedelta
from neo4j import GraphDatabase

# --- Parâmetros ---
N_USERS      = 20
P_ISOLATED   = 0.15               # fração de usuários sem nenhuma aresta
NEO4J_URI    = 'neo4j://127.0.0.1:7687'
NEO4J_USER   = 'neo4j'
NEO4J_PASS   = '12345678'
NEO4J_DB   = 'pmd'    

# --- Inicialização ---
fake    = Faker("pt_BR")
driver  = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def gerar_usuarios(n):
    users = []
    hoje  = date.today()
    for _ in range(n):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        age = hoje.year - dob.year - ((hoje.month, hoje.day) < (dob.month, dob.day))
        min_reg = dob + timedelta(days=18*365)
        reg_date = fake.date_between_dates(date_start=min_reg, date_end=hoje)
        users.append({
            "id": str(random.randint(1, 20)),
            "name": fake.name(),
            "age": age,
            "dob": dob.isoformat(),
            "reg_date": reg_date.isoformat(),
            "city": fake.city()
        })
    return users


def criar_nos(tx, users):
    tx.run("""
    UNWIND $users AS u
    CREATE (:User {
        id: u.id,
        name: u.name,
        age: u.age,
        dob: date(u.dob),
        reg_date: date(u.reg_date),
        city: u.city
    })
    """, users=users)


def criar_arestas(tx, rels):
    tx.run("""
    UNWIND $pairs AS p
    MATCH (a:User {id: p.source}), (b:User {id: p.target})
    CREATE (a)-[:CONNECTED_TO]->(b)
    """, pairs=rels)

def creates_cycle(src, tgt, edges_map):
    # percorre a cadeia de destinos a partir de tgt
    visited = set()
    current = tgt
    while current in edges_map:
        if current == src:
            return True
        if current in visited:
            break
        visited.add(current)
        current = edges_map[current]
    return False

def criar_nos(tx, users):
    tx.run("""
    UNWIND $users AS u
    CREATE (:User {
        id: u.id,
        name: u.name,
        age: u.age,
        dob: date(u.dob),
        reg_date: date(u.reg_date),
        city: u.city
    })
    """, users=users)

def main():
    users = gerar_usuarios(N_USERS)
    ids   = [u["id"] for u in users]

    n_iso       = int(N_USERS * P_ISOLATED)
    isolated    = set(random.sample(ids, n_iso))
    connected   = [uid for uid in ids if uid not in isolated]

    edges_map = {}
    for src in connected:
        candidates = [t for t in connected if t != src]
        random.shuffle(candidates)
        for tgt in candidates:
            if src not in edges_map and not creates_cycle(src, tgt, edges_map):
                edges_map[src] = tgt
                break

    rels = [{"source": s, "target": t} for s, t in edges_map.items()]

    with driver.session(database=NEO4J_DB) as sess:
        # limpa dados antigos (opcional)
        sess.run("MATCH (n:User) DETACH DELETE n")

        # cria nós
        sess.write_transaction(criar_nos, users)

        # cria arestas
        if rels:
            sess.write_transaction(criar_arestas, rels)


main()
