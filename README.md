**Universidade Federal de São Carlos \- Campus Sorocaba**   
Bacharelado em Ciência da Computação 

Processamento massivo de banco de dados

Prof. Dra. Sahudy Montenegro González

![][image1]

Pedro Henrique Bianco Schneider \- 800467  
Nicolas Benitiz \- 813037

## Casa de apostas \- BETs

Sorocaba 

18/06/2025

# Objetivo e Proposta

Nossa proposta é simular o funcionamento de uma casa de apostas (BET), com o intuito de demonstrar de forma mais clara, computacional e lógica como ocorre toda a orquestração dos ganhos, como o esquema é lucrativo e como o topo da pirâmide (pessoa mais famosa e com poder maior de influência) ganha mais dinheiro conforme mais pessoas, que entraram no site por sua indicação, perdem dinheiro na plataforma.

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

# Requisitos mínimos

1. Utilizar dois modelos de dados NoSQL diferentes para armazenamento ou um modelo Apache Spark.

	**R:** Contemplado, pois iremos utilizar mongoDB e neo4j.

2. Integração direta entre as tecnologias escolhidas: usar os conectores disponíveis.  
   **R:** Teremos uma aplicação que fará a relação entre ambos bancos de dados. Exemplo de consulta: quanto o usuário X já ganhou sobre as perdas do usuário Z? Seria necessário verificar no neo4j se existe relacionamento entre estas duas arestas e, se sim, qual a porcentagem de retorno ele recebe para cada perda de Z. Após isso, seria necessário consultar no mongoDB todas as apostas do usuário Z, aplicar a porcentagem sobre os valores apostados e somar os resultados.  
     
3. Interface não é necessária\!  
   **R:** Combinado.

# Tecnologias utilizadas

Por que as tecnologias escolhidas são as melhores para atender a sua aplicação?

Por não enfrentar as limitações dos bancos de dados relacionais, um banco de dados não relacional oferece uma estrutura mais flexível, capaz de armazenar dados semi-estruturados e com natureza hierárquica. Isso o torna mais adequado à nossa proposta, considerando que lidamos com um grande volume de dados, com uma frequência muito maior de inserções do que de consultas, além de uma hierarquia bem definida entre nós. Essa hierarquia possui uma grande profundidade, o que torna a estrutura em árvore mais adequada do que o modelo relacional. Dessa forma, vamos trabalhar com: 

1. **MongoDB**, pelos seguintes motivos: nível de afinidade (tecnologia já vista em aula e prática com os exercícios), possibilidade de criar índices para campos em comum. Poderemos, por exemplo, criar um índice para o tipo de jogo, para verificar com maior rapidez quais são os jogos que mais estão gerando lucro para a casa de apostas. Além disso, a depender do jogo, podem haver campos extra e específicos para cada jogo. Por exemplo: no caça-níquel, existe o conceito de “semi-vitória”, que ocorre quando a roleta tem parcialmente itens iguais. Será necessário armazenar qual foi a porcentagem de vitória do usuário para estes casos. Além disso, no black jack, por exemplo, iremos armazenar quais cartas o jogador obteve em sua vitória, trazendo para cada tipo de jogo uma especificidade. Por isso, não é possível utilizar um banco de dados relacional para a aplicação.  
2. **Neo4j**, pois como iremos trabalhar com hierarquia e relacionamento entre nós (indicações entre pessoas), vamos nos estruturar sobre uma árvore como estrutura de dados principal. Cada nó contém informações de cadastro de cada usuário: nome, idade, data de nascimento, data de cadastro na plataforma, cidade etc.  
3. **Python**, como aplicação que fará a integração entre os dois bancos de dados não relacionais. Optamos por ele pela facilidade em desenvolver na linguagem, e pela existência de libs que fazem integração com mongoDB e neo4j.

![image](https://github.com/user-attachments/assets/5eb53a53-a30c-4e04-ade7-893ff9b2791c)

# Fonte de dados

As fontes de dados serão obtidas de diversas formas e de diversas fontes, usaremos por exemplo, uma coletânea de nomes relacionados à casa de apostas que estão em alta no mundo de hoje obtidos por exemplo em [Noticias](https://www.terra.com.br/diversao/gente/virginia-carlinhos-maia-caua-reymond-e-mais-famosos-revista-traz-a-tona-caches-milionarios-de-influenciadores-e-artistas-para-divulgar-apostas,ce07d7d4c486c246f16f8cf7f2416db4pni604vr.html) , além de alguns coletados em sites como: [Gov](https://www.ssa.gov/oact/babynames/limits.html) e [IBGE](https://censo2010.ibge.gov.br/nomes/) devido ao volume necessário. Para idade, por exemplo, iremos gerar de forma automática por código. Cidades serão coletadas na [Wikipedia](https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil). Datas de nascimento serão geradas por código. Dados de jogos serão gerados automaticamente por código e com foco específico em cada jogo, exemplo: 🎰 🎰 🍒.

# Consultas possíveis:

1. Quais jogos mais dão lucro para a BET?  
2. Quais são os usuários que mais receberam dinheiro a partir da perda dos outros?  
3. Quais são os usuários que mais receberam dinheiro somente a partir de apostas? Pode ser interessante para identificar se um usuário está utilizando métodos ilícitos para ganhar as apostas.  
4. Qual usuário conseguiu trazer mais novos usuários diretos?  
5. Qual a porcentagem de usuários que utilizam código?  
6. Qual a porcentagem de vitória para cada jogo?  
7. Qual usuário conseguiu trazer mais novos usuários diretos e indiretos?  
8. Em quais horários a casa de apostas registra maior porcentagem de derrotas?  
9. Quanto um usuário específico já ganhou por conta de perdas de usuários que usam seu cupom?

# Tipos de jogos armazenados no MongoDB:

1. Caça-níquel: porcentagem de vitória, reels (ex: \[ "🍒", "🍒", "🔔" \]), identificador da máquina  
2. Poker: quantidade de jogadores na mesa, mao (ex: \["A♠", "K♠"\])  
3. Roleta: tipo de aposta (por cor, por número), número escolhido, cor escolhida  
4. Blackjack: cartas do jogador (ex: \["9♣", "K♦"\]), cartas do dealer (ex: \["7♠", "10♣"\])  
5. Aposta esportiva: resultado apostado (vitória de um time, ou empate), resultado real, placar exato esperado, placar exato real.  
   

Podem ser criados ou removidos tipos de jogos no decorrer da realização do projeto.

