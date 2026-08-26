# 📐 Arquitetura Técnica - Painel Transparência TJRR

Este documento descreve a arquitetura técnica, fluxo de dados, pipeline de processamento e estratégia de gerenciamento de memória do **Painel Transparência TJRR**.

---

## 🏗️ Visão Geral da Arquitetura

O sistema é construído sobre uma arquitetura modular em Python dividida em 5 camadas principais:

```text
[ Arquivos CSV em dados/ ]
          │
          ▼ (data_loader.py)
[ DataFrame Base Bruto ]
          │
          ▼ (transformations.py - @st.cache_resource)
[ Singleton DataFrames: df & df_long (float32/category) ]
          │
          ▼ (filters.py)
[ DataFrames Filtrados Dinamicamente ]
          │
      ┌───┴──────────────────────────────┐
      ▼ (charts.py & app.py)             ▼ (app.py - format_detail_df)
[ Visualizações Gráficas & Dashboard ] [ Tabela de Detalhamento & Exportação ]
```

---

## 🧩 Módulos do Sistema

### 1. `data_loader.py` (Carregamento de Dados)
- Responsável por varrer o diretório `dados/` e ler múltiplos arquivos `.csv`.
- Implementa tratamento automático de cabeçalhos do TJRR (identificando a linha correta de nomes de colunas e ignorando metadados de consulta).
- Normaliza valores numéricos no padrão PT-BR (`1.234,56` -> `1234.56`).

### 2. `transformations.py` (Engenharia de Recursos e Cache Singleton)
- Processa o DataFrame bruto e constrói o formato *melted/long* (`df_long`), associando cada registro de remuneração ao tipo de verba (`Remuneração Paradigma`, `Indenizações`, `Previdência Oficial`, etc.).
- **Otimização de RAM**: Converte colunas textuais categóricas para o dtype `category` do Pandas e valores monetários para `float32`.
- Remove colunas temporárias para manter o menor *footprint* de memória possível.

### 3. `filters.py` (Motor de Filtragem)
- Gerencia os filtros da barra lateral (*Ano, Mês/Arquivo, Servidor, Categoria, Cargo, Vínculo, Setor e Tipo de Verba*).
- Executa a filtragem em tempo real sobre o `df_long` com suporte a buscas por sub-string (*case-insensitive*).

### 4. `charts.py` (Geração de Gráficos e Métricas)
- Constrói os gráficos interativos do Plotly Express (Pizza de Créditos, Pizza de Débitos e Linha do Tempo de Evolução).
- Aplica ordenação e encurtamento inteligente de rótulos (`TipoLegend`), formatando legendas em **2 colunas horizontais** com `entrywidthmode="fraction"`.
- Calcula os agregados financeiros e históricos para o **Painel de Indenizações**.

### 5. `app.py` (Interface do Usuário & Layout Responsivo)
- Ponto de entrada do Streamlit (`st.set_page_config`, CSS global e renderização).
- Implementa o **Header compacto** com citações da fonte pública oficial.
- Injeta o layout em **CSS Grid / Flexbox** com suporte total a **Media Queries** para telas de smartphone (< 991px).
- Formata a tabela de detalhamento (`format_detail_df`) reduzindo a exibição por padrão para o último registro por servidor.

---

## ⚡ Estratégia de Gerenciamento de Memória (RAM)

No Streamlit Cloud, instâncias gratuitas possuem limite estrito de 1.0 GB de RAM. Para evitar exceções de estouro de memória (*OOM Killed / Resource Limits*):

1. **`@st.cache_resource` para DataFrames Base**:
   - Em vez de usar `@st.cache_data` (que serializa e duplica cópias em memória em cada rerun), utilizamos `@st.cache_resource` nas funções `load_cached` e `prepare_cached`.
   - Isso armazena um ponteiro singleton compartilhado em memória, reduzindo o consumo adicional por rerun para **0 bytes**.

2. **Detalhamento Otimizado**:
   - A tabela de detalhamento aplica a filtragem `.groupby(nome_col).last()`, exibindo por padrão apenas o registro mais recente de cada servidor (~1.700 linhas em vez de 58.000 linhas).

3. **Garbage Collection Ativo**:
   - Execução explícita de `gc.collect()` e registro de métricas de RAM em tempo real via `logger.info()` e `resource.getrusage()`.
