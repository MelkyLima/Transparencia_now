# 🤝 Guia de Contribuição - Painel Transparência TJRR

Ficamos muito felizes pelo seu interesse em contribuir com o **Painel Transparência TJRR**! Toda ajuda para aprimorar o portal, otimizar a performance ou melhorar a visualização dos dados públicos é extremamente bem-vinda.

---

## 🛠️ Como Posso Contribuir?

### 1. Relatar Bugs ou Problemas
Caso encontre um bug, um cálculo inconsistente ou uma falha de layout:
- Abra uma **Issue** no GitHub.
- Descreva detalhadamente o problema encontrado.
- Se possível, inclua capturas de tela e informações sobre o dispositivo/navegador.

### 2. Sugerir Novas Funcionalidades
Sugestões de melhorias visuais, novos gráficos ou opções de filtros adicionais são sempre apreciadas.
- Abra uma **Issue** com a tag `enhancement` descrevendo a funcionalidade proposta e seu caso de uso.

### 3. Enviar Código (Pull Request)

Se você deseja enviar uma melhoria de código:

1. **Faça um Fork** do repositório no GitHub.
2. **Crie uma Branch** para sua modificação:
   ```bash
   git checkout -b minha-feature-ou-fix
   ```
3. **Faça as alterações necessárias** mantendo o estilo de código limpo e legível.
4. **Valide a sintaxe do código**:
   Antes de commitar, execute a verificação de compilação do Python:
   ```bash
   py -m py_compile app.py transformations.py filters.py charts.py data_loader.py utils.py
   ```
5. **Faça o Commit** das suas alterações com mensagens claras:
   ```bash
   git commit -m "Adiciona novo gráfico comparativo por cargo"
   ```
6. **Envie para o seu Fork** no GitHub:
   ```bash
   git push origin minha-feature-ou-fix
   ```
7. **Abra um Pull Request (PR)** apontando para a branch `main` do repositório oficial.

---

## 📝 Diretrizes de Código

- **Comentários e Documentação**: Preserve docstrings e comentários relevantes sobre a regra de negócio.
- **Tipagem Estática**: Utilize type hints do Python sempre que criar novas funções.
- **Otimização de Memória**: Ao manusear DataFrames no Pandas, utilize os tipos de dados otimizados (`float32` para valores monetários e `category` para colunas com valores repetitivos) para evitar gargalos no Streamlit Cloud.

Muito obrigado por ajudar a manter a transparência pública ainda mais acessível! 🚀
