# G10-Brasil-equipo12-CommunityLab
CommunityLab 🤖💬
Motor Inteligente de Transformação e Distribuição para Comunidades Digitais
Hackathon ONE G10 · Equipe G10-BRASIL-equipe 12

📥 Formato de Entrada e Tipos de Dados
Tipos de Mensagens Suportadas
O motor de processamento categoriza as interações da comunidade em 4 tipos principais:

depoimento: Relatos de conquistas, aprovações em vagas e casos de sucesso dos alunos.

pergunta_tecnica: Dúvidas sobre código, frameworks (LangGraph, OCI, Gemini) ou infraestrutura.

feedback: Sugestões, elogios e críticas sobre a dinâmica do programa.

interacao_geral: Debates espontâneos e conversas informais nos canais.

Estrutura do Payload / PDF de Entrada
JSON
{
  "origem_comunidade": "Discord_Grupo_ONE_G10",
  "periodo_referencia": "Semana_04",
  "interacoes": [
    {
      "autor": "Nome do Aluno",
      "canal": "#canal-origem",
      "tipo": "depoimento | pergunta_tecnica | feedback | interacao_geral",
      "texto": "Conteúdo bruto da mensagem"
    }
  ]
}
