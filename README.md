# 🏛️ Painel Transparência TJRR

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://remuneracoes-tjrr.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Ativo-brightgreen.svg)

> **Portal de Análise Remuneratória e Consulta de Dados das Folhas de Pagamento do Tribunal de Justiça de Roraima (TJRR)**.

O **Painel Transparência TJRR** é um sistema web interativo desenvolvido em Python e Streamlit para extração, consolidação, filtragem e visualização gráfica avançada de dados remuneratórios do Poder Judiciário de Roraima.

---

## 📌 Fonte Oficial dos Dados

Todos os dados apresentados neste painel são provenientes do portal de transparência pública mantido pelo Poder Judiciário do Estado de Roraima:

👉 **[https://remuneracoes.tjrr.jus.br](https://remuneracoes.tjrr.jus.br)**

A ferramenta consolida as informações das folhas de pagamento disponibilizadas publicamente, em estrita conformidade com a **Lei de Acesso à Informação (Lei nº 12.527/2011)** e resoluções do **Conselho Nacional de Justiça (CNJ)**.

---

## ✨ Principais Funcionalidades

### 💼 1. Dashboard Financeiro Consolidado
- **Três Cartões de KPIs**:
  - 🟢 **Total de Créditos (Entradas)**: Soma das remunerações brutas, subsídios, vantagens e gratificações.
  - 🔴 **Total de Débitos (Descontos)**: Soma do Imposto de Renda, Previdência Oficial, Retenções por Teto e Descontos Diversos.
  - 🔵 **Rendimento Líquido**: Valor efetivamente recebido pelos servidores.
- **Tabelas Categorizadas**: Exibição em tabelas independentes com destaques visuais para Entradas e Saídas.

### 🏖️ 2. Painel de Indenizações Dedicado
- Mapeamento isolado e acompanhamento de verbas indenizatórias (*auxílio-alimentação, auxílio-saúde, diárias, substituição, etc.*).
- Comparativo entre o **Último Registro Mensal**, **Últimos 3 Meses**, **Ano Corrente** e **Ano Anterior**.

### 📊 3. Visualizações Gráficas Interativas
- **Gráficos de Pizza (Rosca)**: Distribuição percentual de créditos e débitos com legendas responsivas organizadas em 2 colunas.
- **Gráfico de Evolução Temporal**: Linha do tempo mês a mês ou ano a ano para acompanhamento de tendências financeiras.

### 📋 4. Tabela de Detalhamento & Exportação CSV
- **Filtro Otimizado de Último Registro**: Exibe por padrão apenas o último registro de cada servidor, reduzindo o volume de dados exibidos em mais de 95% sem perder a visão atualizada.
- **Seleção de Colunas Principais**: Alterna entre as 9 colunas prioritárias e o conjunto completo de 18 colunas.
- **Ordenação Decrescente por Data**: Registros organizados a partir da data mais recente (`2026-08`, `2025-12`, ...).
- **Exportação de Dados**: Download de arquivos CSV filtrados com codificação `utf-8-sig` (compatível com Microsoft Excel e Google Planilhas).

### 📱 5. Responsividade Mobile Total
- Layout 100% responsivo construído com CSS Media Queries.
- Empilhamento automático de painéis em smartphones sem cortar textos ou valores numéricos.
- Prevenção de quebra de linha de moedas (`R$` e valores mantidos no mesmo bloco com `white-space: nowrap`).

### ⚡ 6. Otimização Extrema de Memória (RAM)
- Gerenciamento de estado singleton via `@st.cache_resource`, garantindo **0% de duplicidade de DataFrame em RAM** nas interações no Streamlit Cloud.
- Otimização de tipos de dados (`float32` e `category`), reduzindo a pegada de memória em mais de 70%.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.10+
- **Interface Web**: Streamlit
- **Processamento de Dados**: Pandas, NumPy
- **Visualização de Dados**: Plotly Express
- **Estilização**: HTML5 / CSS3 (CSS Grid & Flexbox)

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
Ter o **Python 3.10+** ou superior instalado em sua máquina.

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/MelkyLima/Transparencia_now.git
cd Transparencia_now
```

### Passo 2: Criar e Ativar um Ambiente Virtual (Opcional, mas Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar as Dependências
```bash
pip install -r requirements.txt
```

### Passo 4: Executar a Aplicação
```bash
streamlit run app.py
```
O painel abrirá automaticamente no seu navegador padrão no endereço `http://localhost:8501`.

---

## 📁 Estrutura do Código

```text
Transparencia_now/
├── app.py                  # Ponto de entrada da aplicação Streamlit e renderização da UI
├── transformations.py      # Limpeza de dados, categorização e transformação (df_long)
├── filters.py              # Motor de filtragem da barra lateral e seleção dinâmica
├── charts.py               # Construtor dos gráficos do Plotly e estatísticas de indenizações
├── data_loader.py          # Leitura e parsing de arquivos CSV da pasta dados/
├── utils.py                # Utilitários de formatação de moeda BRL, datas e suporte a strings
├── dados/                  # Diretório contendo os arquivos CSV extraídos do TJRR
├── requirements.txt        # Dependências do projeto
├── README.md               # Documentação principal
├── CONTRIBUTING.md         # Guia de contribuição
└── ARCHITECTURE.md         # Documentação de arquitetura técnica
```

---

## 🤝 Contribuição

Contribuições são super bem-vindas! Sinta-se à vontade para abrir uma *Issue* ou enviar um *Pull Request*. Consulte o arquivo [`CONTRIBUTING.md`](CONTRIBUTING.md) para obter orientações sobre padrões de código e desenvolvimento.

---

## 📜 Licença

Este projeto está licenciado sob a licença **MIT** - consulte o arquivo `LICENSE` para obter mais detalhes.
