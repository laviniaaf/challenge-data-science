# Fase 1: Análise Exploratória

## Pergunta 1: Qual o perfil geral dos dados?

- Sobre os dados: são 500 campanhas com 26 variáveis (9 numéricas contínuas, 5 booleanas, 4 categóricas, 1 temporal, 1 de id).
- Período: ano de 2024, distribuição relativamente uniforme por mês.
- 3 plataformas analisadas: TikTok (≈175 campanhas), Meta (≈170 campanhas) e LinkedIn (≈155 campanhas), com distribuição equilibrada entre os canais.

### Valores faltantes

A coluna tem_legenda (has_caption) apresenta o maior percentual de nulos (9,2%), resultado de dados não coletados em parte das campanhas, o tratamento recomendado é imputar o False, pois a ausência de informação equivale a sem legenda. 
A duracao_video_s (video_duration_s) (7,8%) e proporcao_musica_voz (music_voice_ratio) (7,6%) são nulos pelos mesmos motivos, os criativos de imagem estática não possuem vídeo nem áudio e ambos devem receber tratamento equivalente: criar uma categoria sem_video e uma sem_audio ou manter NaN e isolar esses registros nas análises específicas. 
A taxa_engajamento (engagement_rate) (6,4%) tem nulos por falha de rastreamento e deve ser imputada com a mediana por plataforma. 
O custo_por_clique (cost_per_click) (5,6%) é nulo em campanhas de awareness puro, onde não há cliques e a imputação recomendada é a mediana por objetivo. 
O tempo_medio_visualizacao_s (avg_view_duration_s) (5,4%) mostra a presença de criativos estáticos e deve ser mantido como NaN, também isolado em análises de vídeo. 
A receita (revenue) (5,0%) é ausente em campanhas de awareness sem conversão e deve ser imputada com 0 pois receita ausente equivale a sem receita.

- Critério de decisão: nenhuma coluna supera 10% de nulos então não há justificativa para remover linhas.  
- O padrão dos nulos é disperso (não em bloco), o que indica que os dados se enquadram na categoria Missing At Random, pois, a ausência de um valor não está concentrada em um período, mas distribuída aleatoriamente pelo dataset, e isso significa que os nulos não carregam uma distorsão nos dados então imputar os valores faltantes com mediana, moda ou outra estratégia não distorcerá a análise.

### Outliers

As variáveis com maior concentração de outliers são:
custo_por_clique (cost_per_click), com 14,0% dos registros fora do IQR e máximo de R$26,05, e gasto (spend), com 12,2% e máximo de R$121.226, ambas com skewness elevado (9,93 e 5,94), o que indica distribuições assimétricas à direita e para essas, é recomendado aplicar log-transform antes de modelar, e no caso do custo_por_clique, investigar os registros do LinkedIn, que tendem a inflar o custo. 
As impressoes (impressions) também apresenta 9,0% de outliers e skewness de 11,0, com máximo de 14,05 milhões (valores que representam campanhas de grande escala, logo log-transform é suficiente sem necessidade de remoção). 
Roas tem 5,4% de outliers e máximo de 39,92%, por ser uma variável de saída usada em regressão,é recomendado winsorização no 99° percentil para evitar que valores extremos distorçam o modelo. 
A taxa_cliques (click_rate) e pontuacao_klike (klike_score) são as variáveis mais comportadas: a primeira não tem nenhum outlier e skewness de apenas 0,43 e a segunda tem apenas 0,4% de outliers e skewness negativo (−0,23),o que não exige nenhum tratamento especial.

- Nesse caso os outliers não são erros: Um ROAS de 39.92 ou gasto de R$121k são campanhas de grande porte e a estratégia correta acredito que seria de manter os dados e aplicar transformações como log e winsorize.

---

## Pergunta 2: Quais atributos do criativo mais se correlacionam com boas métricas?

Entre os atributos criativos analisados, o hook nos 3 segundos iniciais é o que apresenta maior correlação com o Klike Score (r = +0,55) e com o CTR (r = +0,26), sendo o fator individual mais determinante para a performance de engajamento. 
A presença de rosto humano vem em segundo lugar, com correlação de +0,39 com o Klike Score e +0,16 com o CTR. 
CTA e legenda também têm correlações com o Klike Score (+0,24 e +0,23), mas com impacto mínimo sobre CTR e ROAS. 
Proporção de música/voz e duração do vídeo apresentam correlações próximas de zero ou negativas com todas as métricas e esses dois atributos, de forma isolada, não diferenciam criativos de alta e baixa performance.

## Analises:

Analisando o impacto por diferença de mediana, o hook é o atributo de maior efeito: criativos com hook saem de um Klike Score mediano de 52,2 para 69,6 (+17,3 pts) e de um CTR de 4,7% para 7,9% (+3,2 pp). 
Em ROAS, porém, o hook reduz pouco (−0,28) indicando que o atributo aumenta cliques mas não necessariamente a conversão. A presença de rosto eleva o Klike Score de 54,9 para 66,3 (+11,4 pts) e o CTR de 5,2% para 7,1% (+1,9 pp). 
O CTA contribui com +7,3 pts no Klike Score e é o único atributo que melhora o ROAS de forma consistente (+0,15). 
A legenda tem impacto menor com +5,7 pts.

- Quanto à densidade de texto, o nível médio é o que entrega melhor Klike Score (66,1), enquanto o nível baixo apresenta o maior CTR (0,067) e o maior ROAS (1,63). 
- Em relação ao retargeting, campanhas direcionadas a audiências já conhecidas entregam ROAS mediano de 2,02 contra 1,27 em campanhas novas (+59%) e CTR de 0,093 contra 0,055 (+69%), confirmando que a audiência qualificada converte melhor.

### Duração do vídeo:

Vídeos com até 10 segundos apresentam o melhor ROAS (2,30) e Klike Score competitivo (61,4). Quando aumenta a duração, o ROAS cai de 1,27 na faixa de 11–20s até 1,03 na faixa de 31–60s. Os vídeos acima de 60 segundos tem no Klike Score (64,2),  que sugere um maior engajamento, mas mantêm ROAS baixo (1,35), logo, engajam mas não convertem na mesma proporção. 
A recomendação com base nessa analise é priorizar versões curtas para campanhas de conversão.

---

## Pergunta 3: Existem padrões diferentes por plataforma?

Sim, pela analise feita o TikTok lidera em retorno financeiro (ROAS 2,64, CPC R$0,52), o Meta fica em segundo (ROAS 1,62, CPC R$0,82) e o LinkedIn tem o pior ROAS (0,53) e o maior CTR (6,7%), os cliques são caros e convertem pouco, tornando-o viável apenas para B2B com ticket alto.

O efeito dos atributos também varia por plataforma: o hook aumenta ROAS no TikTok (+36%) mas reduz no Meta (−0,49) e é neutro no LinkedIn. Quanto ao formato, vertical funciona melhor no TikTok, horizontal no LinkedIn e o Meta aceita qualquer um.

Em termos de categoria de produto, SaaS lidera com ROAS mediano de 3,27, seguido por Lead Gen (2,25) e E-commerce (1,87). App Install (0,48) e Branding (0,00) têm retorno financeiro mínimo ou nulo, que faz sentido, pois essas categorias raramente têm conversão direta em receita. Quanto ao objetivo da campanha, Conversions entrega o maior ROAS (2,30), seguido por Traffic (1,58) e Engagement (0,86). 

---

## Pergunta 4: Visualizações para o time de marketing

Imagens na pasta image. Perguntas respondidas:

### Onde investir? Performance por plataforma

O gráfico evidencia que o TikTok entrega 5× mais ROAS que o LinkedIn com custo por clique 5× menor. Para campanhas de conversão, TikTok é a melhor escolha e o LinkedIn só se justifica para B2B com ticket alto.

### O que colocar no criativo? Impacto dos atributos

O gráfico mostra que o hook nos 3 primeiros segundos é o atributo mais valioso pois aumenta a Klike Score em +17 pts e o CTR em +3,2 pp e a presença de rosto é o segundo  atributo mais valioso. 

### A receita criativa é universal? Hook e Rosto por plataforma

O gráfico revela que o hook aumenta ROAS no TikTok (+36%) mas reduz no Meta. O rosto humano melhora ROAS em todas as plataformas e é o único atributo universal. Foi percebido que não existe um criativo que funcione igualmente bem em todo lugar, então a estratégia precisa ser adaptada por canal.


