import random
import uuid
from pymongo import MongoClient
from collections import Counter
from dotenv import load_dotenv
import math
import os

load_dotenv()

VALORES = {
    **{str(n): n for n in range(2, 11)},
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

def valor_da_carta(carta, is_dealer):
    rank = carta[:-1]
    divisao = 1.2 if is_dealer else 1
    if rank in VALORES:
        return math.ceil(VALORES[rank] / divisao)  
    else:
        return math.ceil(int(rank) / divisao)

def quem_ganhou(placarA, placarB):
    if placarA > placarB:
        return "Time A venceu"
    elif placarB > placarA:
        return "Time B venceu"
    else:
        return "Empate"

def generate_random_bet():
    id_pessoa = str(random.randint(1, 50))
    valor_apostado = round(random.uniform(1, 1000), 2)
    tipo_jogo = random.choice(['roleta', 'caça-níquel', 'poker', 'blackjack', 'aposta esportiva'])
    odd = round(random.uniform(1.1, 3), 2)
    
    dados_variaveis = {}
    cliente_ganhou = False

    if tipo_jogo == 'caça-níquel':
        reels = random.choices(['🍒', '🔔', '🍋', '⭐', '7️⃣'], k=5)

        counts = Counter(reels)
        max_count = max(counts.values())
        porcentagem_vitoria = round(max_count / 5, 2)

        cliente_ganhou = (max_count >= 2)
        dados_variaveis = {
            'porcentagem_vitoria': porcentagem_vitoria,
            'reels': reels,
            'id_maquina': random.randint(1000, 1020)
        }

    elif tipo_jogo == 'poker':
        baralho = [r + s for r in ['A','K','Q','J','10','9','8','7','6','5','4','3','2']
                          for s in ['♠','♥','♦','♣']]
        mao = random.sample(baralho, k=2)
        dados_variaveis = {
            'numero_jogadores': random.randint(2, 10),
            'mao': mao
        }
        cliente_ganhou = random.choices([True] * 30 + [False] * 70)[0]

    elif tipo_jogo == 'roleta':
        tipo_aposta = random.choice(['cor', 'número'])
        if tipo_aposta == 'número':
            numero_escolhido = random.randint(0, 36)
            cor_escolhida    = None
        else:
            cor_escolhida    = random.choice(['vermelho','preto','verde'])
            numero_escolhido = None

        numero_sorteado = random.randint(0, 36)
        if numero_sorteado == 0:
            cor_sorteada = 'verde'
        else:
            cor_sorteada = 'vermelho' if numero_sorteado in {
                *range(1,11), *range(19,29)
            } else 'preto'

        if tipo_aposta == 'número':
            cliente_ganhou = (numero_escolhido == numero_sorteado)
            prob = 1/37
        else:
            cliente_ganhou = (cor_escolhida == cor_sorteada)
            if cor_escolhida == 'verde':
                prob = 1/37
            else:
                prob = 18/37

        odd = round(1 + prob, 2)

        dados_variaveis = {
            'tipo_aposta':       tipo_aposta,
            'numero_escolhido':  numero_escolhido,
            'cor_escolhida':     cor_escolhida,
            'numero_sorteado':   numero_sorteado,
            'cor_sorteada':      cor_sorteada,
        }


    elif tipo_jogo == 'blackjack':
        baralho = [r + s for r in ['A','K','Q','J','9','8','7','6','5','4','3','2']
                          for s in ['♠','♥','♦','♣']]

        odd = 2
        total_jogador = 0
        mao_jogador = []
        total_dealer  = 0
        mao_dealer = []
        vez_do_jogador = True
        while total_jogador <= 21 and total_dealer <= 21:
            carta = random.choice(baralho)
            baralho.remove(carta)
            
            if vez_do_jogador:
                total_jogador += valor_da_carta(carta, False)
                mao_jogador += [carta]
            else:
                total_dealer += valor_da_carta(carta, True)
                mao_dealer += [carta]
            vez_do_jogador = not vez_do_jogador

        cliente_ganhou = total_jogador <= 21

        dados_variaveis = {
            'cartas_jogador': mao_jogador,
            'cartas_dealer': mao_dealer,
            'total_jogador': total_jogador,
            'total_dealer': total_dealer
        }

    else:
        placar_esperado = (random.randint(0,5), random.randint(0,5))
        placar_real = (random.randint(0,5), random.randint(0,5))
        resultado_apostado = quem_ganhou(placar_esperado[0], placar_esperado[1])
        resultado_real = quem_ganhou(placar_real[0], placar_real[1])
        dados_variaveis = {
            'resultado_apostado': resultado_apostado,
            'resultado_real': resultado_real,
            'placar_esperado': placar_esperado,
            'placar_real': placar_real
        }
        cliente_ganhou = (resultado_apostado == resultado_real)

    aposta = {
        'id_pessoa': id_pessoa,
        'valor_apostado': valor_apostado,
        'cliente_ganhou': cliente_ganhou,
        'tipo_jogo': tipo_jogo,
        'odd': odd,
        **dados_variaveis
    }
    if tipo_jogo == 'caça-níquel':
        del aposta["odd"]
        del aposta["cliente_ganhou"]

    return aposta
def insert_bets(n=1000, uri=os.getenv("URI_MONGODB"), db_name=os.getenv("MONGO_DB_NAME"), coll_name='apostas'):
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[coll_name]
    bets = [generate_random_bet() for _ in range(n)]
    result = collection.insert_many(bets)
    print(f'Inseridas {len(result.inserted_ids)} apostas.')

if __name__ == '__main__':
    insert_bets(1000)
