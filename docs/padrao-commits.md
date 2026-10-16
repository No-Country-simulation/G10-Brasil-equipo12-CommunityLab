# Padrão de Commits

Projeto: G10 Brasil · Equipe 12 · CommunityLab

Este documento define como todo o time escreve as mensagens de commit. Seguir o mesmo padrão deixa o histórico do projeto organizado e fácil de entender para todos.

## Formato

```
tipo: descrição curta do que foi feito
```

## Tipos permitidos

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| `feat:` | Funcionalidade nova ou algo novo no projeto | `feat: adiciona chamada de teste à API da Groq` |
| `fix:` | Correção de um erro | `fix: corrige leitura da chave no arquivo .env` |
| `docs:` | Mudanças só em documentação (README, arquivos da pasta `docs`) | `docs: explica a estrutura de pastas do projeto` |

Se o time precisar de outros tipos (por exemplo, para reorganizar código ou ajustar configurações), combinem em grupo e adicionem aqui.

## Regras

1. **Sempre começar com o tipo**, seguido de dois pontos e um espaço (`feat: `).
2. **Escrever em português**, em letras minúsculas depois do tipo.
3. **Ser curto e direto**: ideal até 70 caracteres.
4. **Usar o verbo no presente**: "adiciona", "corrige", "atualiza" (e não "adicionei" ou "adicionando").
5. **Sem ponto final** no fim da mensagem.
6. **Um assunto por commit**: se mudou duas coisas diferentes, faça dois commits.
7. **Nunca commitar o arquivo `.env`** nem qualquer chave ou senha. Ele já está no `.gitignore`, mas confira com `git status` antes de enviar.

## Exemplos bons ✅

```
feat: cria estrutura de pastas do projeto
feat: adiciona primeiro prompt de classificação
fix: corrige erro 401 ao chamar a API
docs: adiciona padrão de commits na pasta docs
```

## Exemplos ruins ❌

| Mensagem | Problema |
|----------|----------|
| `ajustes` | Não diz o que mudou e não tem tipo |
| `Feat: Adicionei coisas.` | Maiúsculas, verbo no passado e ponto final |
| `fix: corrige bug, adiciona prompt e atualiza README` | Três assuntos em um commit só |
| `update` | Sem tipo e sem descrição |

## Como fazer um commit

No terminal do VS Code:

```bash
git add .
git commit -m "feat: adiciona chamada de teste à API da Groq"
git push
```

Antes do `git add .`, rode `git status` para ver o que será enviado.
