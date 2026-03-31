# Painel Web (CSV)

Painel simples para ler automaticamente **todos os arquivos `.csv`** de uma pasta e gerar resumos (totais gerais, por grupo e por mês), com tabelas e gráficos.

## Como rodar

1) Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

2) Execute o painel:

```bash
streamlit run app.py
```

3) No painel (barra lateral):
- Informe a **pasta** onde estão os CSVs (por padrão, usa a pasta atual).
- Selecione a **coluna para agrupar** (ex.: *tipo de pagamento*, *setor*, *cargo*).
- Selecione 1 ou mais **colunas de valor** para somar (ex.: *Total de Créditos (6)*, *Rendimento Líquido (12)*).

## Observações sobre o formato dos seus CSVs

Se o CSV tiver uma primeira linha do tipo `"Data da Consulta";"dd/mm/aaaa hh:mm";`, o app ignora essa linha e usa a segunda linha como cabeçalho.
O app também tenta extrair o **mês** do nome do arquivo (ex.: `01-26.csv` -> `2026-01`) para montar a série mensal.

