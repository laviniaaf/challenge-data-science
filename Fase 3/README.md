# Fase 3: Sistema de Recomendações

Sistema que analisa uma campanha e gera sugestões para melhorar o Klike Score.

---

## Como usar

### Via CLI (terminal)

```bash
cd Fase\ 3/

python engine.py

# Campanhas por ID
python engine.py KLK-0001 KLK-0020 KLK-0042
```

### Via notebook interativo

```bash
pip install pandas numpy matplotlib seaborn jupyter
jupyter notebook recommendations.ipynb
```

---

## Arquitetura

### Estrutura interna

O `KlikeEngine` é composto por cinco métodos. O `__init__` inicializa os benchmarks por plataforma a partir do dataset histórico. O `_preprocess` normaliza os tipos booleanos. O `_compute_benchmarks` calcula as medianas e os deltas de Klike Score, CTR e ROAS por plataforma para cada atributo. O `recomendar` aplica as 9 regras e retorna a lista ordenada por impacto. O `relatorio` formata o resultado para exibição no terminal ou notebook.

### As 9 regras de recomendação

O engine aplica até 9 regras por campanha, cada uma acionada por uma condição específica. As regras de maior confiança são as de hook (acionada quando `tem_hook == False`) e rosto humano (`tem_rosto == False`), pois são os atributos com maior delta histórico em todas as plataformas. Call-to-action (`tem_cta == False`) e legenda (`tem_legenda == False`) têm confiança média. Densidade de texto e formato são comparados ao melhor valor observado para a plataforma da campanha, também com confiança média exceto quando o delta for grande. Duração do vídeo e proporção música/voz têm confiança baixa, pois os padrões são mais ruidosos e as recomendações são tratadas como sugestão, não prescrição. Por fim, a regra de retargeting é acionada quando a campanha é de prospecção e o delta de ROAS para audiência quente na mesma plataforma supera 0,2.

### Quantificação das recomendações

O impacto de cada recomendação é calculado como a diferença entre a mediana do Klike Score das campanhas que têm o atributo e a mediana das que não têm, dentro da mesma plataforma. Usamos mediana por plataforma em vez de média global por dois motivos: a mediana é robusta a outliers (o ROAS pode chegar a 39,92 em campanhas SaaS no TikTok) e o mesmo atributo tem impacto diferente dependendo do canal.

O engine trata cada plataforma de forma independente. O hook, por exemplo, gera um delta de +17,0 pts no TikTok, +17,7 pts no Meta e +13,7 pts no LinkedIn. O rosto humano contribui com +8,4 pts no TikTok, +13,1 pts no Meta e +10,8 pts no LinkedIn. O formato é o caso mais extremo de variação: vertical entrega +12,7 pts sobre o quadrado no TikTok, mas no LinkedIn penaliza em 11,5 pts em relação ao horizontal. Por isso a regra de formato é especialmente contextual e nunca recomenda o mesmo valor para todas as plataformas.

---

## Limitações 

Os deltas de cada regra são calculados de forma independente, o que faz o "potencial total" somar impactos que na prática se sobrepõem e o ganho real ao aplicar todas as recomendações juntas será menor do que a soma individual. O LinkedIn tem apenas 83 campanhas no dataset, o que resulta em benchmarks menos estáveis para essa plataforma. 
Os impactos são correlacionais: campanhas que usam hook podem ter outras características que contribuem para o resultado, e sem um experimento A/B controlado não é possível isolar o efeito de cada atributo. E, as regras de duração e áudio têm padrões mais ruidosos e devem ser tratadas como sugestão exploratória, não como prescrição.
