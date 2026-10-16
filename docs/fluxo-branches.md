# Fluxo de Trabalho com Branches

Projeto: G10 Brasil · Equipe 12 · CommunityLab

## O que é uma branch?

Imagine que o projeto é um **caderno oficial** (a branch `main`). Se todo mundo escrever nele ao mesmo tempo, as páginas ficam bagunçadas.

Uma **branch** é uma **cópia de rascunho** do caderno. Cada pessoa trabalha no seu rascunho e, quando a tarefa está pronta e conferida, o rascunho é copiado para o caderno oficial.

## Por que isso é importante para nós?

- Somos várias pessoas mexendo no mesmo projeto.
- Se duas pessoas editarem o mesmo arquivo na `main` ao mesmo tempo, pode acontecer um **conflito**, e resolver conflito é difícil para quem está começando.
- Se alguém enviar um erro direto para a `main`, todo mundo recebe o erro.
- Com branches, a `main` fica sempre limpa e funcionando.

## Como saber em qual branch estou?

Use qualquer um destes jeitos:

1. **Canto inferior esquerdo do VS Code**: aparece o nome da branch (ex.: `main`). Clicando nele, dá para trocar de branch.
2. **Terminal:** `git branch`. A branch atual aparece com um asterisco (`*`).
3. **Terminal:** `git status`. A primeira linha mostra `On branch ...`.

**Regra de ouro:** antes de começar a mexer, olhe em qual branch você está. Se estiver na `main`, crie sua branch primeiro.

## Passo a passo para cada tarefa

**1. Atualize a main:**
```bash
git switch main
git pull
```

**2. Crie sua branch** (um nome por tarefa):
```bash
git switch -c feat/teste-groq
```

**3. Trabalhe normalmente e faça commits** seguindo o padrão do arquivo `padrao-commits.md`:
```bash
git add .
git commit -m "feat: adiciona chamada de teste à API da Groq"
```

**4. Envie sua branch para o GitHub:**
```bash
git push -u origin feat/teste-groq
```
(Nos próximos envios, basta `git push`.)

**5. Abra um Pull Request no GitHub:** na página do repositório, aparece um botão para criar o Pull Request da sua branch. Peça para alguém do time dar uma olhada.

**6. Depois que o Pull Request for aceito (merge), limpe e atualize:**
```bash
git switch main
git pull
```

## Nome das branches

Formato: `tipo/descricao-curta`, usando os mesmos tipos dos commits:

| Exemplo | Para quê |
|---------|----------|
| `feat/teste-groq` | funcionalidade nova |
| `fix/leitura-env` | correção de erro |
| `docs/readme` | documentação |

Sem espaços, sem acentos, tudo minúsculo e com hífen.

## Regras do time

1. **Não enviar direto para a `main`.** Sempre usar uma branch e Pull Request.
2. **Uma branch por tarefa**, com nome claro.
3. **Antes de começar qualquer tarefa:** `git switch main` e `git pull`.
4. **Nunca enviar o arquivo `.env`.** O repositório é público, então qualquer chave enviada por engano fica visível para todo mundo.
5. Em caso de dúvida ou mensagem de erro estranha, **pare e pergunte no grupo** antes de forçar qualquer comando.

## Se aparecer um erro ao enviar

- **`rejected` ou `failed to push`:** alguém enviou algo antes de você. Rode `git pull` e tente `git push` de novo.
- **`conflict`:** peça ajuda a alguém do time antes de mexer nos arquivos.
