# Regras de roteamento

Define qual tipo de mensagem pode gerar qual ativo de distribuição. Este documento é uma **proposta para aprovação do time** (cartão da Sprint 3). A seção 4 lista as decisões em aberto.

## 1. Tabela: tipo de mensagem → ativos

Os cinco tipos aceitos pelo motor estão em `src/schemas.py` (`TIPOS_INTERACAO`).

| Tipo | Post de LinkedIn | Destaque de newsletter | Sugestão de FAQ | Observação |
| :--- | :-: | :-: | :-: | :--- |
| `depoimento` | ✅ | ✅ | — | Conquistas, aprovações e casos de sucesso |
| `entrega_projeto` | ✅ | ✅ | — | O motor aceita este tipo, mas o dataset de 50 não tem mensagens dele |
| `feedback` | — | ✅ | — | Sugestões, elogios e críticas |
| `pergunta_tecnica` | — | — | ✅ | O FAQ sugere só o tema da dúvida, sem a solução técnica |
| `interacao_geral` | — | — | — | Entra no total de interações e no sentimento, mas não gera ativo |

Um ativo só existe se houver pelo menos uma mensagem de um dos tipos marcados. Sem material, o ativo vem `null`, sem erro. Isso já é o que o prompt pede hoje (`COMO PREENCHER`, em `src/prompts.py`).

## 2. Casos especiais

- **Relato de dificuldade pessoal** (desânimo, insegurança). Serve só para o sentimento. O nome do autor nunca aparece no post nem na newsletter, e a dúvida técnica, se houver, vira um tema de FAQ anônimo. No dataset de 50, são `MSG_011` e `MSG_049` (tipo `interacao_geral`) e `MSG_028` (tipo `pergunta_tecnica`): **o tipo sozinho não separa esses casos**.
- **Mensagem vaga ou curta demais** (por exemplo, "Achei legal o encontro de hoje."): não vira ativo. O guia do FAQ já pede `null` nesse caso.
- **Mensagem vazia ou repetida:** removida na limpeza, antes do roteamento.
- **Conquista que não aconteceu ainda** (proposta, segunda etapa de seleção): pode gerar ativo, mas sem aumentar o tamanho da conquista (regra 6 do prompt).

## 3. Como funciona hoje e o que a Sprint 3 acrescenta

**Hoje:** o roteamento acontece **dentro do prompt**. A LLM recebe todas as mensagens da amostra e decide quais ativos preencher, seguindo as regras acima. A pontuação de relevância (0 a 100) só ordena as mensagens e escolhe a amostra (até 10, com cotas de 5 relatos, 3 dúvidas e 2 outras). **Depois** da resposta, uma segunda checagem em código (`src/roteamento.py`, chamada em `src/pipeline.py`) descarta qualquer ativo sem mensagem do tipo certo no lote e qualquer post ou newsletter que cite quem só fez pergunta técnica ou conversa geral (decisões 7 e 8). Cada descarte vai para o log e tem teste automático (`tests/test_roteamento.py`).

**Ainda proposto para a Sprint 3:** o código calcular a rota de cada mensagem pelo tipo **antes** de chamar a LLM, e pedir só os ativos que têm material. Isso ainda não existe: a checagem acima corrige o resultado, mas não evita o pedido à LLM.

## 4. Decisões do time (03/11/2026)

1. **Rota só pelo tipo.** A relevância (0 a 100) continua servindo para ordenar e escolher a amostra, mas não decide se um ativo existe.
2. **Gabarito do `DEMO_08`** (feedback, "Achei legal o encontro de hoje."): passa de "Resumo de satisfação" para "Nenhum ativo (só sentimento)". A mensagem é um feedback, então a rota a permite, mas é vaga demais para virar newsletter (seção 2).
3. **Sentimento não é critério de rota no MVP.** O exemplo do desafio ("sentimento extremamente positivo → Case de Sucesso") é apresentado como exemplo de ramificação. A nossa ramificação é pelo tipo da mensagem. O sentimento continua no resumo da comunidade, mas só existe depois da LLM e vale para o lote inteiro, não para cada mensagem. A escolha será explicada no README.
4. **"Dúvida recorrente".** Qualquer `pergunta_tecnica` pode gerar FAQ. O motor não mede recorrência, e o contrato (`src/schemas.py`) tem uma única sugestão de FAQ por lote, então a LLM escolhe um tema entre as dúvidas da amostra. **Medir recorrência fica como evolução futura.**
5. **Relato de dificuldade, em camadas.**
   - **Código** (a implementar na Sprint 3): mensagens `interacao_geral` não geram nenhum ativo, então o nome do autor não precisa chegar à LLM. Elas seguem para a análise com o autor como "Participante" (a troca acontece depois da limpeza e da amostra). Isso protege `MSG_011` e `MSG_049` sem depender do prompt.
   - **Prompt:** a regra 5 continua valendo para o resto, incluindo `MSG_028` (`pergunta_tecnica`), cujo nome só poderia aparecer no campo `origem` do FAQ, que é interno (vai para a mentoria).
   - **Conferência:** o checklist de fidelidade audita esses casos e será repetido antes da entrega.
   - **Limite conhecido:** um relato de dificuldade com tipo `depoimento` ou `feedback` depende só do prompt. O nome que aparece dentro do texto da própria mensagem também não é removido pelo código.
6. **Feedback na amostra** (a implementar na Sprint 3). Hoje as 20 mensagens do grupo "outros" do dataset (11 `interacao_geral` e 9 `feedback`) pontuam todas 10 e empatam, então as 2 vagas vão para as primeiras da ordem do arquivo. Na amostra atual deram `MSG_003` (feedback) e `MSG_004` ("Bom dia, pessoal!"), por acaso. Decisão: dividir o grupo em 1 vaga para `feedback` e 1 para `interacao_geral`, passando a vaga ao outro se um deles não existir. Assim o feedback que alimenta a newsletter não depende da ordem do arquivo, e ainda sobra uma vaga de conversa geral para o sentimento. Exige ajustar `PESOS_AMOSTRA` (`src/relevancia.py`) e os testes de cotas.

7. **Checagem de nomes depois da LLM** (implementada na Sprint 3, em `src/roteamento.py`). Post ou newsletter que cite o nome de um autor cujas mensagens, no lote enviado à LLM, são **só** `pergunta_tecnica` ou `interacao_geral` é descartado (o ativo vem `null`) e o descarte vai para o log. Quem também tem `depoimento`, `entrega_projeto` ou `feedback` no lote não entra nessa regra. Como a comparação funciona:
   - Vale o **nome completo** sempre. Vale também o **primeiro nome**, desde que tenha 3 letras ou mais e que nenhuma pessoa com `depoimento`, `entrega_projeto` ou `feedback` no lote tenha o mesmo primeiro nome (para dois "Rafael" não derrubarem um post legítimo). Nesse caso só o nome completo conta. *Decisão final do time (05/11/2026): o primeiro nome e o nome completo seguem a mesma regra (ver decisão 10).*
   - A busca ignora maiúsculas e acentos e exige a palavra inteira ("ana" não casa com "banana"). Nomes de usuário sem espaço (por exemplo, `luan_dev22`) só valem inteiros. "Participante" é ignorado.
   - Só são conferidos o título e a copy do post e a chamada e o resumo da newsletter. A seção da newsletter (texto fixo, como "Vitória da Semana") e a origem do FAQ (campo interno) **não** são conferidas.
   - O log registra qual ativo foi descartado e o motivo, **sem o nome da pessoa**.
   - **Limite:** a checagem só enxerga a amostra enviada à LLM, e só pega o nome escrito. Um relato de dificuldade com tipo `depoimento` ou `feedback` continua dependendo do prompt e do teste manual (decisão 9).
8. **Cada ativo só existe se houver mensagem do tipo certo** (implementada na Sprint 3, em `src/roteamento.py`; cartão "Validar no código que cada ativo só existe se houver mensagem do tipo certo"). Depois da resposta da LLM, o código confere a tabela da seção 1 sobre o lote enviado à LLM: post sem `depoimento` ou `entrega_projeto`, newsletter sem `depoimento`, `entrega_projeto` ou `feedback`, e FAQ sem `pergunta_tecnica` são descartados e registrados no log. A regra 7 faz parte dessa mesma validação, que tem 25 testes automáticos (`tests/test_roteamento.py`).
   - **Limite:** o código confere o **tipo**, não a qualidade. Uma mensagem vaga do tipo `feedback` (caso `DEMO_08`) continua podendo gerar newsletter se a LLM insistir, e depende do prompt, como na decisão 2.
9. **Teste manual de privacidade** (antes da entrega, e de novo depois do congelamento dos prompts). É manual porque a saída da LLM varia. Como fazer:
   - Criar um arquivo de entrada com 2 ou 3 mensagens sintéticas de dificuldade marcadas como `depoimento` ou `feedback`, mais um depoimento comum, para que o post exista. Exemplo (nomes fictícios, fora do dataset):

```json
{
  "origem_comunidade": "Teste_Privacidade",
  "periodo_referencia": "Semana_Teste",
  "interacoes": [
    {"autor": "Larissa Quintela", "canal": "#geral", "tipo": "depoimento",
     "texto": "Estou pensando em desistir do curso. Trabalho o dia todo, chego cansada e sinto que todo mundo aprende mais rápido do que eu."},
    {"autor": "Heitor Salgado", "canal": "#feedback-geral", "tipo": "feedback",
     "texto": "Me sinto perdido nas aulas de LangGraph e tenho vergonha de perguntar. Acho que não vou conseguir acompanhar."},
    {"autor": "Paulo Neves", "canal": "#conquistas-e-vagas", "tipo": "depoimento",
     "texto": "Terminei meu primeiro projeto com Streamlit e já está no ar! Obrigado a quem me ajudou nos erros de deploy."}
  ]
}
```

   - Rodar **sem** `--oci`: `python -m src.pipeline <arquivo> --periodo Semana_Teste`. Repetir 3 vezes.
   - **Passa** se os nomes de Larissa Quintela e Heitor Salgado não aparecem no `post_linkedin` nem no `destaque_newsletter_semanal` em nenhuma das 3 execuções. O nome de Paulo Neves pode aparecer.
   - Registrar a data, o commit e o resultado (por exemplo, na seção de reexecução do checklist de fidelidade). Se um nome aparecer, abrir um cartão: o prompt precisa de ajuste, e este é o caso que a regra 7 não cobre sozinha, porque esses autores têm `depoimento` ou `feedback`.

10. **Privacidade, LGPD e autorização para publicar nome** (decisão final do time em 05/11/2026).
   - **Hoje:** o dataset e os nomes são fictícios e, por isso, a equipe entende que não há dado pessoal (ver [dataset_simulado.md](dataset_simulado.md), seções 7 e 8). Este documento descreve as práticas do projeto e **não afirma conformidade jurídica** com a LGPD (Lei nº 13.709/2018): isso depende de análise com orientação jurídica ou do encarregado de dados (DPO) da organização, caso o motor seja usado com dados reais.
   - **Com dados reais**, nome e sobrenome identificam uma pessoa e são dado pessoal. O primeiro nome, numa comunidade pequena, também pode identificar. Por isso a regra vale para os dois, e a checagem de nomes da decisão 7 olha os dois.
   - **Autorização para publicar (decisão do time):** o nome só pode ser usado seguindo esta regra, e ela vale **igualmente para o primeiro nome e para o nome completo**. Nenhum post, destaque de newsletter ou outro conteúdo público pode sair com o nome (primeiro nome ou nome e sobrenome) de uma pessoa sem a **autorização prévia dela** para essa divulgação. A autorização deve ser específica para esse uso (post, newsletter), registrada, e poder ser retirada a qualquer momento, em linha com o consentimento da LGPD (art. 5º, XII; art. 7º, I; art. 8º). Sem autorização, o conteúdo sai sem o nome ou não é publicado. O prompt do LinkedIn já diz que a publicação com nome depende da autorização, conferida na curadoria humana (`prompts/linkedin.md`).
   - **O que o código faz e não faz:** o código **não verifica** autorização. O contrato (`src/schemas.py`) não tem campo para isso. A conferência é um passo **humano** antes de publicar. O que o código garante é a decisão 7: quem só fez pergunta ou conversa não é citado.
   - **Dados enviados ao provedor de LLM:** o texto da amostra, com os nomes dos autores, é enviado à Groq. Só as mensagens `interacao_geral` seguem com o autor trocado por "Participante". Com dados reais, é preciso definir a base legal, verificar o tratamento pelo provedor e pela OCI e anonimizar o que for possível (ver [dataset_simulado.md](dataset_simulado.md), seção 7).
   - **Sem pontos em aberto:** a autorização é obrigatória para qualquer publicação com nome, seja o primeiro nome ou o nome completo. Por isso a checagem da decisão 7 trata os dois da mesma forma.

### Evolução futura

- Registrar a autorização de cada pessoa e mostrar um aviso na interface de curadoria (Streamlit, Sprint 4) antes de aprovar um conteúdo com nome.
- Medir recorrência de dúvidas (mesmo tema em mais de uma mensagem).
- Montar o campo `origem` do FAQ pelo código, e não pela LLM.

## 5. Conferência com o gabarito dos casos de demo

A tabela da seção 1 concorda com `docs/resultados_esperados.md`: `DEMO_01` e `DEMO_09` (depoimento) → post; `DEMO_02`, `DEMO_06`, `DEMO_07` e `DEMO_10` (pergunta técnica) → FAQ; `DEMO_03` (feedback) → newsletter; `DEMO_08` (feedback vago) → nenhum ativo.
