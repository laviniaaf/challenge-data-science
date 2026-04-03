# Fase 2: Modelagem preditiva

## Decisão da construção de dois modelos

O primeiro desafio da modelagem foi decidir quais informações o modelo poderia usar. Algumas variáveis, como CTR, ROAS e impressões, só existem depois que a campanha já rodou então usá-las para prever o Klike Score seria uma forma de data leakage (o modelo aprenderia com informações que não existem no momento da decisão).

Por isso foram criados dois modelos com propósitos distintos:
O modelo completo utiliza tanto os atributos criativos quanto as métricas de resultado, atingindo R²=0,793, mas ele é pouco util em produção porque você não pode prever o ROAS de uma campanha usando o próprio ROAS. O modelo pré-campanha usa apenas características que existem antes do lançamento e alcança R²=0,618 e é o que tem valor real, pois permite recomendar melhorias antes de gastar qualquer budget.

---

## 1. Feature Engineering

O modelo pré-campanha foi construído com 18 features divididas em quatro grupos:
As colunas booleanas de atributos criativos (tem_hook, tem_rosto, tem_cta, tem_legenda, e_retargeting) foram convertidas de sim/não para 1/0, pois apresentaram alta correlação com o Klike Score na análise exploratória. 
A densidade de texto recebeu encoding ordinal (low=0, medium=1, high=2) para preservar a ordem semântica. 
As variáveis categóricas de: plataforma, categoria, objetivo, faixa etária e formato foram transformadas via one-hot encoding, pois os efeitos de plataforma são grandes e não-lineares. Duração do vídeo, proporção música/voz, mês e trimestre completam o conjunto como variáveis numéricas de controle.

Além das features originais, três novas variáveis foram criadas para capturar efeitos que a EDA identificou: a feature hook_face (tem_hook multiplicado por tem_rosto) captura o efeito composto entre os dois atributos mais importantes: hook e rosto juntos superam a soma isolada de cada um. 
A feature hook_cta (tem_hook multiplicado por tem_cta) modela o combo entre capturar atenção e direcionar ação, que amplifica a conversão. 
A is_short_video marca explicitamente os vídeos com até 10 segundos, que apresentaram o melhor roas na análise da Fase 1.

Para o modelo completo, as variáveis de resultado (impressões, gasto, conversões, receita) receberam transformação logarítmica por serem assimétricas, e o ROAS foi winsorizado no percentil 99 para evitar que outliers extremos dominassem o ajuste.

---

## 2. Modelo

Três algoritmos foram comparados via validação cruzada com 5 folds: 
- Ridge (modelo linear, usado como referência)
- Random Forest 
- Gradient Boosting (GBM)
No cenário pré-campanha, o GBM obteve o melhor R² de validação (0,618), com RMSE de 9,56 pts e MAE de 7,70 pts. O Random Forest ficou próximo (R²=0,584) mas com R² de treino de 0,912, indicando mais overfitting. O Ridge teve o menor R² (0,578) por ser incapaz de capturar interações entre variáveis sem feature engineering manual extensivo.

O GBM foi escolhido por três razões. Primeiro, tem o melhor desempenho de validação entre os modelos pré-campanha. Segundo, aprende automaticamente que o efeito do hook não é o mesmo em todas as plataformas, sem precisar que isso seja especificado manualmente. Terceiro, tem overfitting controlado: o gap entre R²_treino (0,975) e R²_CV (0,618) é esperado para n=500 com árvores, e a combinação de max_depth=4 com learning_rate=0,05 limita o problema.

---

## 3. Avaliação

No hold-out de 20% (100 campanhas), o GBM pré-campanha atingiu RMSE de 10,19 pts, MAE de aproximadamente 7,7 pts e R²=0,541, ou seja, 54% da variância do Klike Score é explicada apenas por decisões criativas que a equipe controla.

Um R² entre 0,54 e 0,62 é um resultado válido por três motivos. O erro médio de 7,7 pts é menor do que o delta entre criativos com e sem hook (17 pts), o que significa que o modelo detecta o sinal que importa. 

---

## 4. Feature Importance

As sete variáveis mais importantes confirmam os achados da Fase 1: has_hook lidera com importância de 0,305, seguido por densidade_texto e has_face empatados em 0,110.
A proporcao_musica_voz aparece em quarto (0,069), seguida pela feature de interação hook_cta (0,064), duracao_video_s (0,056) e tem_legenda (0,054). O fato de o modelo ter aprendido os mesmos padrões identificados na análise exploratória aumenta a confiança nos resultados.

