# challenge-data-science

Resolução de um challenge de data science, desenvolvido ao longo de 4 fases: análise exploratória, modelagem preditiva, sistema de recomendações e visão de produto.

---

## Sobre o repositório:

O objetivo é analisar os dados de campanhas publicitárias, construir um modelo para prever o Klike Score e criar um sistema de recomendações para ajudar times criativos a melhorarem seus anúncios.

O dataset original estava em inglês. Optei por traduzi-lo para português para facilitar o desenvolvimento durante o período curto do challenge: mesmo com inglês intermediário, trabalhar com nomes de variáveis em português acelerou mais a análise e reduziu erros de interpretação nas métricas.

---

## Estrutura do projeto

```
challenge-data-science/
├── Fase 1/    # análise exploratória dos dados
├── Fase 2/    # modelo preditivo 
├── Fase 3/    # sistema de recomendações 
└── Fase 4/    # visão de produto
```

---

## Como baixar e rodar

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd challenge-data-science
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Rodar cada fase

**Fase 1 e 2** — abrir os notebooks no Jupyter:
```bash
jupyter notebook
```

**Fase 3** — rodar o sistema de recomendações direto no terminal:
```bash
cd "Fase 3"
python engine.py
```
---

## Fases do projeto

**Fase 1** analisa o perfil dos dados: distribuição por plataforma, valores faltantes, outliers e quais atributos criativos mais se correlacionam com boas métricas.

**Fase 2** constrói um modelo preditivo para prever o Klike Score antes do lançamento da campanha, usando apenas informações disponíveis na fase de criação do anúncio.

**Fase 3** transforma os insights da análise em um sistema de recomendações que, dado uma campanha, sugere melhorias priorizadas por impacto estimado.

**Fase 4** responde às perguntas de visão de produto: quais features extrairia do vídeo original, como colocaria o engine em produção e o que faria com mais tempo.
