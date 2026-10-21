# G10-Brasil-equipo12-CommunityLab

## 🏛️ Arquitetura do Sistema

O fluxo de dados do **CommunityLab** segue a seguinte estrutura:

1. **Entrada:** Captura de mensagens do Discord ou PDFs de relatórios.
2. **Motor de Ingestão:** Pré-processamento e limpeza dos dados brutos.
3. **Processamento IA:** Categorização e análise de sentimento via Gemini e LangGraph.
4. **Distribuição & Armazenamento:** Envio para canais específicos e gravação na Oracle Cloud (OCI).

```mermaid
graph TD
    A[Entrada: Discord / PDF] --> B[Motor de Ingestão]
    B --> C[Processamento IA - Gemini & LangGraph]
    C --> D{Classificação}
    D -->|Depoimento| E[Canal de Destaques]
    D -->|Dúvida Técnica| F[Suporte / Mentores]
    D -->|Feedback| G[Métricas Gerais]
    C --> H[Armazenamento - Oracle Cloud OCI]
'''
