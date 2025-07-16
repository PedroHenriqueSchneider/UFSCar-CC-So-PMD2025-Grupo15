**Universidade Federal de São Carlos \- Campus Sorocaba**   
Bacharelado em Ciência da Computação 

Processamento massivo de banco de dados

Prof. Dra. Sahudy Montenegro González

Pedro Henrique Bianco Schneider \- 800467  
Nicolas Benitiz \- 813037

## Casa de apostas \- BETs

Sorocaba 

18/06/2025

# Resumo 
Este relatório detalha o desenvolvimento de um protótipo para simular o funcionamento das apostas e ganhos de uma casa de apostas online (BET). O contexto é o crescimento expressivo dessas plataformas no Brasil e a falta de transparência sobre seus modelos de lucratividade, especialmente os que envolvem redes de influenciadores. O objetivo principal do trabalho é demonstrar, de forma computacional e lógica, como ocorre a orquestração dos ganhos, com foco no sistema de comissões por indicação. A metodologia adotada envolve a integração de dois bancos de dados NoSQL, MongoDB para armazenar a variedade de dados de apostas e Neo4j para modelar a hierarquia de relacionamentos entre usuários. 

Como resultados principais, o sistema permite executar consultas que revelam os jogos mais lucrativos, os usuários que mais ganham com perdas alheias e a eficácia das redes de indicação. A conclusão central é que a combinação de tecnologias NoSQL é uma abordagem eficaz para modelar e expor os mecanismos financeiros que tornam as casas de apostas e suas redes de afiliados um negócio altamente lucrativo.

# Introdução
Uma casa de apostas, mais conhecida como cassino virtual no Brasil concentra diferentes jogos e estilos de apostas. Existem jogos que simulam o funcionamento dos cassinos reais, com maquininhas e bingos e existem os criados com foco em ambientes virtuais, como apostas esportivas e o joguinho do avião. Alguns dos jogos de apostas mais famosos atualmente são conhecidos como: Jogo do Tigrinho (Fortune Tiger), Plinko, Mines, Aviator, JetX, Fortune Ox, Spaceman e Penalty Shoot Out. 

Como exemplificação do funcionamento de alguns desses jogos, usaremos o jogo do tigrinho, como é o mais famoso e também uma aposta esportiva.
O Fortune Tiger é conhecido como um caça-níquel clássico, ao jogá-lo, o usuário precisa alinhar 3 imagens iguais nas 3 fileiras que aparecem. Cada rodada possui cinco linhas de pagamento disponíveis: três na horizontal e duas na diagonal, além de seis símbolos chineses de pagamento, incluindo um especial, que é justamente o tigrinho – uma espécie de coringa. ([link](https://www.em.com.br/apostas/melhores-jogos-de-apostas/)). Um dos motivos do Fortune Tiger ser considerado superior aos demais jogos de aposta são seus multiplicadores, que aumentam o palpite inicial em até 10 vezes. A conclusão central é que a combinação de tecnologias NoSQL é uma abordagem eficaz para modelar e expor os mecanismos financeiros que tornam as casas de apostas e suas redes de afiliados um negócio altamente lucrativo.

Toda aposta precisa ter algumas informações comuns, como: quem apostou, quanto foi apostado, se o cliente ganhou, tipo de jogo (eg. bingo, roleta, caça-níquel), qual foi a odd da aposta etc. A odd é o quanto o jogador ganha em retorno. Por exemplo, se a odd é de 2x, e a aposta vitoriosa foi de R$50.00, então o cliente irá receber R$100.00.

Além disso, existe uma estratégia um pouco ardilosa utilizada pelas BETs para incentivar que as pessoas divulguem o site: cada pessoa possui um código único que pode ser utilizado por novos clientes, e, para todo dinheiro perdido pelo usuário que está utilizando seu código, ela recebe 10% em retorno. Exemplo: Júnior utilizou o código de Rogério no site de apostas. Júnior apostou R$100.00 no caça-níquel e perdeu. Portanto, Rogério recebe R$10.00 do site porque o perdedor entrou no site utilizando seu código.  
Para tornar o projeto mais interessante, vamos considerar que se existe caminho entre usuário X e Z, e eles não são diretamente relacionados, então X recebe 50% sobre o valor recebido pelo usuário que o liga até Z.   
Exemplo:

![image](https://github.com/user-attachments/assets/054dc524-34cc-4ccf-9ccc-4f4a113eda2f)

Se Z perde uma aposta:

1. O usuário B recebe 10% sobre o valor apostado por Z  
2. O usuário A recebe 5% (10% x 0.5) sobre o valor apostado por Z  
3. O usuário X recebe 2.5% (5% x 0.5) sobre o valor apostado por Z.

Desta forma, para cada aposta perdida, podemos descobrir quais usuários deverão receber alguma quantia, e quanto deverão receber.  
Vale ressaltar que um usuário pode apostar na BET sem usar o cupom de ninguém. Desta forma, nosso grafo é desconexo.

### Requisitos mínimos

1. Utilizar dois modelos de dados NoSQL diferentes para armazenamento ou um modelo Apache Spark.

	**R:** Contemplado, pois iremos utilizar mongoDB e neo4j.

2. Integração direta entre as tecnologias escolhidas: usar os conectores disponíveis.  
   **R:** Teremos uma aplicação que fará a relação entre ambos bancos de dados. Exemplo de consulta: quanto o usuário X já ganhou sobre as perdas do usuário Z? Seria necessário verificar no neo4j se existe relacionamento entre estas duas arestas e, se sim, qual a porcentagem de retorno ele recebe para cada perda de Z. Após isso, seria necessário consultar no mongoDB todas as apostas do usuário Z, aplicar a porcentagem sobre os valores apostados e somar os resultados.

### Tipos de jogos armazenados:

O nosso escopo será focado **apenas** nos cinco jogos abaixo e irão se concentrar **apenas** nas seguintes formas de vitória.

1. Caça-níquel: porcentagem de vitória, reels (ex: \[ "🍒", "🍒", "🔔" \]), identificador da máquina  
2. Poker: quantidade de jogadores na mesa, mao (ex: \["A♠", "K♠"\])  
3. Roleta: tipo de aposta (por cor, por número), número escolhido, cor escolhida  
4. Blackjack: cartas do jogador (ex: \["9♣", "K♦"\]), cartas do dealer (ex: \["7♠", "10♣"\])  
5. Aposta esportiva: resultado apostado (vitória de um time, ou empate), resultado real, placar exato esperado, placar exato real.

### Funcionamento dos jogos especificados e lógica de vitória

Para que a simulação determine se uma aposta foi vitoriosa ou não, cada jogo possui uma lógica específica de vitória, conforme nosso escopo e detalhado abaixo:

**Caça-níquel**: A vitória ocorre quando os símbolos (reels) se alinham em uma das combinações pré-definidas como vitoriosas (linhas de pagamento). Por exemplo, obter [ "🍒", "🍒", "🍒" ] em uma linha horizontal ou diagonal resulta em um ganho. A porcentagem de vitória geral da máquina controla a frequência desses resultados a longo prazo.

**Poker**: O jogador vence a rodada se, ao final, sua mão de cartas, combinada com as cartas comunitárias na mesa, formar o jogo de cinco cartas mais forte que o de todos os outros jogadores na mesa, seguindo a classificação padrão das mãos de poker (ex: um Full House vence um Flush).

**Roleta**: O jogador ganha se sua aposta corresponder ao resultado sorteado. Se o tipo de aposta foi "por cor" e a cor escolhida foi 'vermelho', ele vence se a bola cair em qualquer número vermelho. Se a aposta foi em um número escolhido específico, ele só vence se a bola cair exatamente naquele número.

**Blackjack**: O objetivo é derrotar o dealer (a "casa"). O jogador vence se a soma das suas cartas for mais próxima de 21 do que a soma das cartas do dealer, sem ultrapassar 21. O jogador também ganha automaticamente se o dealer ultrapassar 21 (estourar).

**Aposta Esportiva**: A vitória é direta e ocorre quando a previsão do jogador se concretiza. O resultado apostado (ex: vitória do Time A) deve ser idêntico ao resultado real. Em apostas mais específicas, o placar exato esperado deve corresponder perfeitamente ao placar exato real da partida.

# Objetivos

### Objetivo Geral

Simular o funcionamento de uma casa de apostas (BET) para demonstrar de forma clara, computacional e lógica como ocorre a orquestração dos ganhos e a lucratividade do esquema de indicações.

### Objetivos Específicos

- **Modelar** a estrutura de dados de usuários e suas relações de indicação utilizando um banco de dados de grafos (Neo4j).
- **Estruturar** o armazenamento de diferentes tipos de jogos e apostas em um banco de dados de documentos (MongoDB), garantindo flexibilidade de esquema.
- **Desenvolver** scripts em Python para gerar dados sintéticos (usuários, apostas, resultados) a partir de fontes públicas e algoritmos.
- **Implementar** a lógica de negócio, incluindo o cálculo de odds e a distribuição de comissões por perdas na rede de indicações.
Criar um conjunto de consultas analíticas para extrair informações estratégicas do sistema simulado.

# Planejamento Inicial (Fase Intermediária I)

### Escopo e Delimitação

- **Incluso no Escopo**: A modelagem e implementação do back-end da simulação, incluindo a criação dos bancos de dados, a integração via Python, a lógica de jogos (Caça-níquel, Poker, Roleta, Blackjack, Aposta Esportiva) e o sistema de comissão hierárquico. A geração de dados e a execução de consultas pré-definidas.
- **Fora do Escopo**: O desenvolvimento de qualquer tipo de interface gráfica para o usuário final (conforme requisito "Interface não é necessária!"). A simulação não envolverá transações financeiras reais.
  
**Metodologia Proposta**

A metodologia proposta é o desenvolvimento de um protótipo funcional. A abordagem se baseia na utilização de tecnologias NoSQL, onde o Neo4j é empregado para gerenciar a complexidade dos relacionamentos hierárquicos e o MongoDB para armazenar o grande volume de dados transacionais e semi-estruturados das apostas. Uma aplicação em Python servirá como camada intermediária para integrar os dois bancos e aplicar a lógica de negócio, além de gerar os dados e plotar os gráficos sobre eles.

# Fundamentação teórica

### Por que as tecnologias escolhidas são as melhores para atender a aplicação?

Por não enfrentar as limitações dos bancos de dados relacionais, um banco de dados não relacional oferece uma estrutura mais flexível, capaz de armazenar dados semi-estruturados e com natureza hierárquica. Isso o torna mais adequado à nossa proposta, considerando que lidamos com um grande volume de dados, com uma frequência muito maior de inserções do que de consultas, além de uma hierarquia bem definida entre nós. Essa hierarquia possui uma grande profundidade, o que torna a estrutura em árvore mais adequada do que o modelo relacional. Dessa forma, vamos trabalhar com: 

1. **MongoDB**, pelos seguintes motivos: nível de afinidade (tecnologia já vista em aula e prática com os exercícios), possibilidade de criar índices para campos em comum. Poderemos, por exemplo, criar um índice para o tipo de jogo, para verificar com maior rapidez quais são os jogos que mais estão gerando lucro para a casa de apostas. Além disso, a depender do jogo, podem haver campos extra e específicos para cada jogo. Por exemplo: no caça-níquel, existe o conceito de “semi-vitória”, que ocorre quando a roleta tem parcialmente itens iguais. Será necessário armazenar qual foi a porcentagem de vitória do usuário para estes casos. Além disso, no black jack, por exemplo, iremos armazenar quais cartas o jogador obteve em sua vitória, trazendo para cada tipo de jogo uma especificidade. Por isso, não é possível utilizar um banco de dados relacional para a aplicação.  
2. **Neo4j**, pois como iremos trabalhar com hierarquia e relacionamento entre nós (indicações entre pessoas), vamos nos estruturar sobre uma árvore como estrutura de dados principal. Cada nó contém informações de cadastro de cada usuário: nome, idade, data de nascimento, data de cadastro na plataforma, cidade etc.  
3. **Python**, como aplicação que fará a integração entre os dois bancos de dados não relacionais. Optamos por ele pela facilidade em desenvolver na linguagem, e pela existência de libs que fazem integração com mongoDB e neo4j, "pymongo" e "neo4j", respectivamente.

## Discussão sobre as técnologias utilizadas

### Análise teórica das escolhas (MongoDB)

**Problema 1**: A Heterogeneidade dos Dados de Jogos

O Problema Teórico: Os jogos simulados são inerentemente diferentes. Uma aposta no Caça-níquel precisa armazenar os símbolos que apareceram nos rolos (ex: reels: ["🍒", "🍒", "🔔"]). Uma aposta em Roleta precisa armazenar a cor ou o número escolhido (ex: tipo_aposta: "cor", valor: "vermelho"). Uma aposta em Blackjack precisa das cartas do jogador e do dealer.

A Ineficiência de um Banco Relacional (SQL): Em um banco de dados relacional (como MySQL ou PostgreSQL), se tem péssimas opções:

Tabela Única com Colunas Nulas: Criar uma única tabela Apostas com colunas para todos os possíveis campos de todos os jogos (reels, cartas_jogador, cor_escolhida, etc.). Para uma aposta de roleta, as colunas reels e cartas_jogador seriam nulas. Isso gera um desperdício de espaço e uma estrutura de dados "suja" e confusa.

Múltiplas Tabelas: Criar uma tabela para cada tipo de aposta (apostas_caçaniquel, apostas_roleta, etc.). Isso resolve o problema das colunas nulas, mas cria um novo: como consultar de forma eficiente "todas as apostas perdidas pelo usuário X", se elas estão espalhadas em várias tabelas? Seria necessário fazer consultas complexas (com UNION) e a manutenção se tornaria complicada.

A Solução do MongoDB: O modelo de documentos resolve isso de forma elegante. Todas as apostas podem ser armazenadas em uma única "coleção" chamada apostas. Cada documento dentro dessa coleção tem autonomia para ter os campos que precisa.
Documento 1 (Caça-Níquel): { id_usuario: "123", jogo: "Caça-Níquel", valor: 5.00, reels: ["🍒", "🔔", "7️⃣"] }
Documento 2 (Roleta): { id_usuario: "456", jogo: "Roleta", valor: 10.00, tipo_aposta: "numero", numero_escolhido: 25}

Conclusão Teórica: O MongoDB foi escolhido porque seu esquema dinâmico se adapta perfeitamente à natureza heterogênea dos dados das apostas, permitindo armazenar informações variadas em uma única coleção de forma eficiente e organizada, sem a rigidez imposta por um esquema de tabelas fixas.

**Problema 2**: Alto Volume e Velocidade de Inserção

O Problema Teórico: Casas de apostas geram um volume massivo de transações (apostas) em um curto espaço de tempo. A aplicação precisa "escrever" (inserir) dados de forma muito rápida e contínua.

A Solução do MongoDB: MongoDB é projetado para escalabilidade horizontal (sharding). Isso significa que, à medida que o volume de apostas cresce para bilhões de registros, se pode distribuir a coleção de apostas por múltiplos servidores. Isso permite que o sistema mantenha uma alta performance de escrita e leitura, simplesmente adicionando mais máquinas à sua infraestrutura, um processo que é nativamente suportado pelo MongoDB.

### 2. Análise teórica das escolhas (Neo4j)
   
O Neo4j é um banco de dados orientado a grafos. Sua estrutura fundamental são Nós e Arestas. Nós representam entidades (ex: um Usuário), e Relacionamentos representam como esses nós se conectam (ex: um usuário INDICOU outro).

**Problema 1**: A Natureza Hierárquica das Indicações

O Problema Teórico: O núcleo da análise de comissões é a rede de indicações. "Usuário A indicou B, que indicou C, que indicou Z". Esta é, por definição, uma estrutura de grafo. A pergunta "Quanto o usuário A ganha quando Z perde?" exige que seja percorrido esse caminho de relacionamentos.
A Ineficiência de Outros Bancos:
Em um Banco Relacional (SQL): seria modelado isso com uma chave estrangeira id_indicador na tabela de usuários. Para encontrar o caminho de Z até A, seria necessário executar uma série de JOINs da tabela com ela mesma (chamadas de recursive JOINs ou self-JOINs). Para cada nível de profundidade na hierarquia, a consulta se torna mais lenta e complexa. Em redes profundas, isso se torna impraticável.

Em um Banco de Documentos (MongoDB): seria possível aninhar os indicados dentro de um documento de usuário, mas isso tornaria a consulta reversa ("quem indicou X?") muito difícil. A outra opção é usar o operador $graphLookup, mas ele não é tão performático ou intuitivo quanto uma consulta nativa em um banco de grafos para esse tipo de problema.

A Solução do Neo4j: Neo4j foi criado exatamente para isso. Ele armazena os relacionamentos como elementos de primeira classe. Percorrer o caminho de Z até A é a operação mais fundamental e otimizada que ele pode fazer. A consulta, escrita na linguagem Cypher, é declarativa e intuitiva:
// Encontre o caminho entre o usuário 'A' e o usuário 'Z'
MATCH caminho = (indicador:Usuario {nome: 'A'})-[:INDICOU*]->(perdedor:Usuario {nome: 'Z'})
RETURN caminho
O * no relacionamento [:INDICOU*] significa "percorra este relacionamento por um ou mais níveis de profundidade". O Neo4j executa essa busca com performance excepcional, independentemente de haver 2 ou 20 níveis entre A e Z.

### Conclusão Teórica: 
O Neo4j foi escolhido porque o seu modelo de dados de grafo mapeia diretamente a estrutura hierárquica do problema de indicações. Ele é otimizado para consultas de travessia de grafos (encontrar caminhos e conexões), tornando as perguntas sobre a rede de influenciadores extremamente rápidas e simples de formular, algo que seria proibitivamente lento e complexo em outros modelos de banco de dados.

**Conclusão**: A Sinergia (Por que não usar apenas um?)
Por que não usar só Neo4j para tudo? Porque armazenar bilhões de apostas como nós individuais no Neo4j poluiria o grafo com dados transacionais que não se beneficiam da análise de relacionamentos, tornando as consultas de travessia (seu ponto forte) mais lentas.
Por que não usar só MongoDB para tudo? Porque analisar relações hierárquicas complexas no MongoDB exigiria lógica pesada na aplicação e consultas ineficientes, anulando a agilidade do banco.

Assim:
MongoDB cuida do que faz melhor: armazenar um volume massivo de dados de apostas com estruturas variadas.
Neo4j cuida do que faz melhor: mapear e consultar a rede complexa de relacionamentos e influências entre usuários.

![image](https://github.com/user-attachments/assets/5eb53a53-a30c-4e04-ade7-893ff9b2791c)

# Desenvolvimento

### Descrição das Atividades Realizadas

Conforme o planejamento, a fase inicial do desenvolvimento concentrou-se na configuração do ambiente tecnológico. Os servidores MongoDB e Neo4j foram instalados e configurados.

**Modelagem em Neo4j**: Foi definido um nó do tipo Usuario com propriedades como nome, idade e cidade. As relações de indicação foram modeladas através da aresta :INDICOU, criando uma estrutura de grafo que permite percorrer a árvore de indicações.

**Modelagem em MongoDB**: Foi criada uma coleção chamada apostas. Cada documento nesta coleção representa uma aposta e contém campos comuns (id_usuario, valor_apostado) e campos específicos do jogo, como reels para o "Jogo do Tigrinho" ou placar_real para apostas esportivas.

**Geração de Dados**: Iniciou-se o desenvolvimento de scripts em Python para popular os bancos. Nomes foram extraídos de listas do IBGE, e dados de jogos são gerados aleatoriamente, respeitando a lógica de cada modalidade.

**Apresentação e Análise de Resultados** (Potenciais): O protótipo foi projetado para responder a consultas complexas que cruzam dados dos dois bancos. A aplicação em Python executa a consulta no Neo4j para encontrar, por exemplo, todos os usuários indicados por "X", e depois busca no MongoDB todas as apostas perdidas por esses usuários para calcular a comissão de "X". Os resultados que o sistema pode gerar incluem:

- Um ranking dos jogos que mais geram receita líquida para a BET.
- Uma lista dos principais usuários beneficiados pelo sistema de comissão, com o valor total recebido.
- A porcentagem exata de vitórias para cada jogo, permitindo avaliar seu "equilíbrio".
- O número de usuários diretos e indiretos trazidos por um influenciador específico.

O MongoDB é um banco de dados orientado a documentos. Isso significa que ele armazena dados em estruturas flexíveis do tipo JSON (tecnicamente, BSON), que se assemelham a objetos em programação. Cada aposta no seu sistema pode ser um "documento" individual.

### Fonte de dados

As fontes de dados serão obtidas de diversas formas e de diversas fontes, usaremos por exemplo, uma coletânea de nomes relacionados à casa de apostas que estão em alta no mundo de hoje obtidos por exemplo em [Noticias](https://www.terra.com.br/diversao/gente/virginia-carlinhos-maia-caua-reymond-e-mais-famosos-revista-traz-a-tona-caches-milionarios-de-influenciadores-e-artistas-para-divulgar-apostas,ce07d7d4c486c246f16f8cf7f2416db4pni604vr.html) , além de alguns coletados em sites como: [Gov](https://www.ssa.gov/oact/babynames/limits.html) e [IBGE](https://censo2010.ibge.gov.br/nomes/) devido ao volume necessário. Para idade, por exemplo, iremos gerar de forma automática por código. Cidades serão coletadas na [Wikipedia](https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil). Datas de nascimento serão geradas por código. Dados de jogos serão gerados automaticamente por código e com foco específico em cada jogo, exemplo: 🎰 🎰 🍒.

### Consultas possíveis:

1. Quais jogos mais dão lucro para a BET?  
2. Quais são os usuários que mais receberam dinheiro a partir da perda dos outros?  
3. Quais são os usuários que mais receberam dinheiro somente a partir de apostas? Pode ser interessante para identificar se um usuário está utilizando métodos ilícitos para ganhar as apostas.  
4. Qual usuário conseguiu trazer mais novos usuários diretos?  
5. Qual a porcentagem de usuários que utilizam código?  
6. Qual a porcentagem de vitória para cada jogo?  
7. Qual usuário conseguiu trazer mais novos usuários diretos e indiretos?  
8. Em quais horários a casa de apostas registra maior porcentagem de derrotas?  
9. Quanto um usuário específico já ganhou por conta de perdas de usuários que usam seu cupom?

# Conclusões

### Retomada dos Objetivos
O desenvolvimento do protótipo demonstra que os objetivos propostos são alcançáveis. A arquitetura escolhida permitiu modelar com sucesso tanto os dados transacionais das apostas quanto a complexa rede de relacionamentos, atendendo ao objetivo geral de criar uma simulação funcional para análise.

### Síntese dos Resultados
O trabalho resulta em um sistema capaz de fornecer uma visão clara e quantitativa da distribuição de lucros em uma casa de apostas. A simulação evidencia que o modelo de comissão por perdas é um poderoso motor financeiro, muitas vezes mais significativo do que a própria margem da casa nos jogos.


### Como executar o projeto?

Como requisito mínimo, ter instalado:
MongoDB, 
Neo4j desktop e 
Python 

### Primeira etapa - Configurar Neo4j
1. Preparar ambiente Neo4j. Para isto você deverá:
Criar uma instância na versão 2025.05.0:

[image]

2. Abrir a pasta onde está a instância:
[image]

3. Copiar, colar e descompactar o arquivo “configuracoes_neo4j.zip” (que está no git) neste diretório. Perceba que as pastas plugins e conf serão sobrescritas.
4. Execute.

## Segunda etapa - Configurar MongoDB
Crie um database chamado “pmd-2025”, com um schema chamado “apostas”:

[image]

### Terceira etapa - Gerar dados com Python
Baixe as dependências do projeto executando:
	```pip install -r requirements.txt```
 
Execute os seguintes códigos para gerar dados no neo4j e mongodb:
	```python generator_neo.py```
	```python create_data.py```



