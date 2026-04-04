# Fase 4: Visão de produto

## Pergunta 1: Features adicionais do vídeo original

Com acesso ao arquivo de vídeo, seria possível extrair informações muito mais ricas do que os metadados atuais permitem.

Na parte visual, daria para detectar quantos rostos aparecem e qual o tamanho deles na tela, em vez de apenas saber se tem rosto ou não. Também seria possível analisar o ritmo de cortes do vídeo, as cores predominantes e quanto tempo o produto aparece em cena. O OCR permitiria ler o texto das legendas e analisar quais palavras estão sendo usadas.

No áudio, daria para medir o BPM da música, o volume geral e transcrever o que é falado. Com a transcrição, seria possível detectar se há um CTA verbal e qual o tom da mensagem. Também daria para separar melhor a música da voz, o que tornaria a variável `proporcao_musica_voz` muito mais precisa do que é hoje.

Na parte semântica, embeddings do modelo CLIP transformariam o vídeo em um vetor numérico que representa o conteúdo visual de forma mais completa, permitindo comparar campanhas parecidas e verificar se a legenda está descrevendo bem o que aparece na tela.

Na parte estrutural, o mais relevante seria tornar o hook contínuo: em vez de apenas saber se tem hook ou não, saber o quão forte esse hook é. O mesmo vale para o CTA: saber quando ele aparece no vídeo faz diferença, já que um CTA no início tem comportamento diferente de um no final.

O ganho esperado no modelo seria considerável, elevando o R² pré-campanha de 0,62 para algo próximo de 0,80.

---

## Pergunta 2: Como colocar o Recommendations Engine em produção

O engine precisa funcionar em dois momentos distintos:

O primeiro é quando o usuário está criando uma campanha no painel e precisa de recomendações em tempo real, com resposta em menos de 200ms. O segundo é uma análise em lote feita periodicamente sobre todas as campanhas do histórico, onde a velocidade não é crítica.

Para isso, a proposta seria uma API simples em FastAPI, rodando em Docker, que recebe os dados da campanha e retorna as recomendações. Os benchmarks por plataforma ficariam salvos em cache (Redis) e seriam recalculados uma vez por dia, de madrugada, evitando que esse cálculo aconteça a cada requisição. Um banco PostgreSQL guardaria os dados históricos.

O sistema escala bem porque o engine não guarda estado: para cada campanha nova, ele simplesmente lê os benchmarks do cache e aplica as regras. Não precisa de GPU, então o custo operacional é baixo.

Para melhorar o engine com o tempo, o ideal seria registrar quais recomendações foram aceitas ou ignoradas pelos usuários, e depois de 30 dias comparar o Klike Score real com o estimado. Isso permitiria identificar quais regras estão estimando bem e quais estão exagerando no impacto, e ajustar os benchmarks mensalmente.

---

## Pergunta 3: O que mais faria com mais tempo

A prioridade mais alta seria tentar entender se os resultados que encontramos são causais ou apenas correlações, por exemplo, campanhas com hook podem ter outras características que contribuem para o resultado, como um budget maior. Um teste simples, variando apenas um atributo por vez, seria um caminho para validar isso.

Depois, implementaria as features de vídeo descritas na Pergunta 1, que provavelmente trariam o maior ganho em qualidade do modelo. Também acredito que treinar modelos separados por plataforma, já que TikTok, Meta e LinkedIn possuem um comportamentos bem diferentes, e um modelo único acaba sendo um meio-termo.

Com mais tempo tambem adicionaria intervalos de confiança nas estimativas de impacto, para deixar claro quando uma recomendação é baseada em poucos dados e tem mais incerteza. Também exploraria combinações de atributos, já que hoje as regras são avaliadas de forma independente, mas na prática hook + face + CTA juntos têm um efeito diferente da soma de cada um separado.

Por último, otimizaria os hiperparâmetros do GBM de forma mais sistemática e adicionaria valores SHAP por predição, para conseguir explicar casos específicos quando alguém perguntar por que determinada campanha recebeu aquele score.
