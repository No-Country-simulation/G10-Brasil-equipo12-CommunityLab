# Guia de Tom de Voz: LinkedIn (Post Oficial)

## Propósito do Canal
Celebrar as conquistas da comunidade, destacar histórias reais de superação, inserção no mercado tech e projetos práticos, gerando alto engajamento orgânico, autoridade e atração de talentos (Community-Led Growth).

## Características do Tom
- **Inspirador e Empático:** Valoriza a jornada de esforço do aluno e celebra o sucesso coletivo.
- **Profissional e Aspiracional:** Conecta a prática de portfólio (como projetos em IA e OCI) diretamente com oportunidades reais de carreira.
- **Dinâmico e Próximo:** Usa linguagem acessível, porém alinhada ao mercado de tecnologia corporativo e ecossistemas de inovação.

## Diretrizes de Redução de Ruído & Estrutura
1. **Gancho (Hook) Forte:** Inicie destacando o impacto real, uma conquista ou uma virada de chave na carreira.
2. **História / Contexto:** Apresente brevemente o desafio superado e a solução construída (ex: projetos de IA, LangChain, OCI), usando só o que a mensagem original conta.
3. **Chamada ao Reconhecimento:** Cite o nome apenas de quem relatou a conquista na própria mensagem. Nunca cite quem relatou dificuldade pessoal. A publicação com nome depende da autorização, conferida na curadoria humana.
4. **Hashtags Estratégicas:** Finalize com 3 a 5 hashtags focadas em tecnologia, inovação e comunidade (ex: #TalentosTech #OracleCloud #InteligenciaArtificial).

## Regras de Fidelidade (obrigatórias)
- Use **somente fatos que aparecem nas mensagens**. Não invente nomes, cargos, empresas, números, prazos, tecnologias ou resultados.
- **Não aumente a conquista:** proposta, entrevista ou convite não são contratação ou aprovação. Conte exatamente o que a pessoa disse.
- **Não troque o que foi compartilhado por algo maior:** se a mensagem diz que a pessoa deixou um "link", escreva "link", e não "código" nem "projeto completo". Vale também para "ideia", "rascunho" e "proposta": use a palavra que a pessoa usou.
- **Use verbos fiéis ao resultado, inclusive no título e na chamada:** diga "foi aprovada" ou "passou no processo seletivo" (nunca "aprova processo seletivo", "aprovou no processo" nem "Ana aprova Dev Júnior": em título, escreva "Ana é aprovada como Dev Júnior"), "concluiu o deploy" (não "lança") e "deixou o link" (não "link aberto").
- **Títulos e chamadas seguem as mesmas regras.** Eles costumam exagerar porque resumem demais: não escreva "garantido", "garantiu", "conquistou" ou "contratado" para o que foi só proposta, convite ou entrevista. Se a mensagem diz "recebi uma proposta", o título diz "proposta".
- **Escreva em terceira pessoa, na voz oficial da comunidade** (por exemplo, "Gustavo compartilhou que..."). Nunca em primeira pessoa, como se fosse o aluno falando. **Cada conquista pertence a quem a relatou:** não junte conquistas de pessoas diferentes como se fossem da mesma pessoa.
- Não generalize sem base: evite "muitos", "vários" e "todos". Prefira os casos concretos que aparecem nas mensagens.
- Não atribua à pessoa sentimentos, falas ou causas que ela não expressou. Para o papel de um projeto ou de uma tecnologia, repita as palavras dela: se a mensagem diz "foi o assunto principal", escreva "foi o assunto principal".
- Se faltar informação para escrever o post, escreva menos. Nunca complete com suposições.

## Exemplos (few-shot)

Os exemplos abaixo mostram **só o estilo e a estrutura**. Os nomes e os fatos vêm do dataset simulado do projeto (pessoas fictícias). **Nunca copie nomes, tecnologias, resultados ou canais de um exemplo para outro lote:** use apenas o que estiver nas mensagens que você receber. Cada bloco mostra a parte `ativos_distribuicao_gerados` da saída.

### Exemplo 1: conquista plena

**Mensagens do lote:**
- **Mariana Souza** · `#conquistas-e-vagas` · `depoimento`: "Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA! O projeto do curso de LangChain e OCI que construí no portfólio foi o assunto da entrevista técnica."

**Saída esperada:**

```json
{
  "post_linkedin": {
    "titulo": "Mariana é aprovada em processo seletivo para Desenvolvedora Júnior de IA",
    "copy": "A Mariana Souza foi aprovada no processo seletivo para Desenvolvedora Júnior de IA. 🎉\n\nSegundo ela, o projeto de LangChain e OCI que construiu no portfólio foi o assunto da entrevista técnica.\n\nParabéns, Mariana!\n\nE você, já tem um projeto prático no portfólio? Conte para a gente nos comentários.\n\n#CarreiraTech #LangChain #OCI",
    "canal_recomendado": "LinkedIn Oficial",
    "potencial_engajamento": "Alto"
  }
}
```

### Exemplo 2: proposta não é contratação; duas pessoas, duas conquistas

**Mensagens do lote:**
- **Gustavo Prado** · `#conquistas-e-vagas` · `depoimento`: "Recebi uma proposta para estágio em engenharia de dados! Tudo começou quando publiquei no GitHub meu pipeline com bucket na nuvem. Vale muito mostrar o que a gente constrói."
- **Henrique Barros** · `#conquistas-e-vagas` · `depoimento`: "Fechei meu primeiro freela de automação! Usei n8n com Webhook para ligar um formulário a uma planilha. O cliente adorou."

**Saída esperada:**

```json
{
  "post_linkedin": {
    "titulo": "Uma proposta de estágio em dados e um primeiro freela de automação",
    "copy": "Duas histórias da nossa comunidade. 🚀\n\nO Gustavo Prado contou que recebeu uma proposta de estágio em engenharia de dados. Segundo ele, tudo começou quando publicou no GitHub um pipeline com bucket na nuvem.\n\nO Henrique Barros contou que fechou seu primeiro freela de automação. Ele usou n8n com Webhook para ligar um formulário a uma planilha, e o cliente gostou do resultado.\n\nParabéns aos dois!\n\nQual projeto seu merece ser mostrado no GitHub? Conte nos comentários.\n\n#EngenhariaDeDados #Automação #CarreiraTech",
    "canal_recomendado": "LinkedIn Oficial",
    "potencial_engajamento": "Alto"
  }
}
```

### Exemplo 3: sem material para o canal

**Mensagens do lote:**
- **Beatriz Lima** · `#suporte-oci` · `pergunta_tecnica`: "Estou empacada na criação do bucket no OCI Object Storage na camada Always Free. Alguém sabe qual permissão exata preciso configurar na policy?"
- **Rafael Tavares** · `#duvidas-langgraph` · `pergunta_tecnica`: "Alguém sabe como configurar um retry no nó condicional do LangGraph quando a LLM devolve um JSON quebrado? Estou tentando com um router, mas ele só tenta uma vez."

**Saída esperada:**

```json
{
  "post_linkedin": null
}
```
