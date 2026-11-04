# Gabarito de Ramificações (Roteamento de Conteúdo)

Este documento define as regras de decisão e os ativos de saída correspondentes para cada tipo de mensagem processada pelo motor do **CommunityLab**.

---

## Tabela de Classificação e Ativos

| Classificação | Critérios de Entrada | Ativo de Saída (Output) |
| :--- | :--- | :--- |
| **Alta Relevância** | Contratações, aprovações, conquistas de alunos, conclusão de projetos de destaque. | **Post para LinkedIn** (Texto persuasivo + hashtags) |
| **Média Relevância** | Dúvidas técnicas recorrentes, debates ricos entre alunos, dicas de estudo e boas práticas. | **Newsletter / FAQ Dinâmico** (Resumo formatado) |
| **Baixa Relevância** | Conversas informais, mensagens fora do escopo técnico, interações genéricas. | **Nenhum ativo gerado** (Filtro/Descarte) |

---

## Regras de Roteamento (Lógica do Motor)

1. **Se Entrada = Alta Relevância:**
   - Extrai autor, contexto e citações.
   - Envia para o módulo de geração de post do LinkedIn.

2. **Se Entrada = Média Relevância:**
   - Categoriza o tópico técnico.
   - Formata a resposta/resumo para a Newsletter semanal e banco de dados do FAQ.

3. **Se Entrada = Baixa Relevância:**
   - Ignora a mensagem para economizar chamadas de API e manter o foco do banco.
