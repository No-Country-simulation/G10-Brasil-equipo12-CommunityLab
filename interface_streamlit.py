# interface_streamlit.py
"""Interface de curadoria da Pauta IA, o agente do projeto CommunityLab (passo 1: gerar o conteúdo; passo 2: editar, aprovar ou reprovar cada texto).

Como abrir (na pasta raiz do projeto, com o ambiente virtual ativo):
    streamlit run interface_streamlit.py

Esta tela NÃO envia nada ao OCI. A decisão da pessoa fica num arquivo à parte em saida/ (ignorada pelo Git). A lógica fica em src/interface_logica.py (com testes).
A tela é de propósito simples: quem usa só escolhe as mensagens e gera o conteúdo.
"""
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.ia_service import ErroServicoLLM
from src.interface_logica import (
    altura_do_campo,
    ATIVOS,
    URL_LINKEDIN,
    anonimizar_pessoas,
    autores_do_lote,
    ativos_para_exibir,
    campos_editaveis,
    carregar_lote_de_exemplo,
    carregar_lote_enviado,
    caminho_curadoria,
    clima_da_comunidade,
    decisao_vale,
    exemplos_de_demonstracao,
    executar,
    EXEMPLO_SEM_NOME,
    MOTIVOS_REPROVACAO,
    frase_do_lote,
    montar_motivo,
    nome_do_revisor_valido,
    pacote_aprovado,
    pessoas_citadas_no_ativo,
    registrar_decisao,
    salvar_decisoes,
    tabela_de_mensagens,
    texto_do_ativo,
    texto_para_publicar,
)

# Nome escolhido na votação do time. Para trocar o nome, mude NOME_AGENTE e gere de novo a imagem assets/logo_pauta_ia.png (original do mascote em assets/mascote.svg).
NOME_AGENTE = "Pauta IA"
# Caminhos a partir da pasta deste arquivo (funcionam mesmo que o streamlit seja aberto de outra pasta)
PASTA_ASSETS = Path(__file__).resolve().parent / "assets"
MASCOTE = PASTA_ASSETS / "mascote.png"
LOGO = PASTA_ASSETS / "logo_pauta_ia.png"

st.set_page_config(page_title=f"{NOME_AGENTE} · Curadoria", page_icon=str(MASCOTE) if MASCOTE.is_file() else "🧪", layout="wide", initial_sidebar_state="collapsed")

# Etiqueta amarela com texto preto (cores da marca), largura máxima da página e topo centralizado. As demais cores ficam em .streamlit/config.toml.
st.markdown(
    "<style>"
    ".etiqueta{background:#FFD966;color:#111111;font-weight:700;padding:4px 14px;border-radius:999px;display:inline-block;}"
    # Em tela larga, as linhas de texto ficariam compridas demais: limita e centraliza a página
    "[data-testid='stMainBlockContainer'],.block-container{max-width:1500px;margin-left:auto;margin-right:auto;}"
    ".topo{text-align:center;} .topo h3{font-weight:700;margin:0 0 .6rem 0;} .topo p{max-width:820px;margin:0 auto .6rem auto;text-wrap:balance;}"
    ".topo .pequeno{font-size:.85rem;color:#6b7280;}"
    # título só para leitores de tela (o nome visível é a imagem da logo)
    ".so-leitor{position:absolute;left:-9999px;}"
    "</style>",
    unsafe_allow_html=True,
)

# Topo centralizado: logo (mascote + nome, o "IA" em azul), chamada e explicação. Só entram no HTML textos fixos do código.
if LOGO.is_file():
    _, centro_logo, _ = st.columns([1, 1, 1])
    centro_logo.image(str(LOGO), width="stretch")
    st.markdown(f"<h1 class='so-leitor'>{NOME_AGENTE}</h1>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align:center'>🧪 {NOME_AGENTE}</h1>", unsafe_allow_html=True)

st.markdown(
    "<div class='topo'>"
    f"<h3>A {NOME_AGENTE} transforma o que a sua comunidade conta em conteúdo pronto para publicar.</h3>"
    f"<p>Escolha as mensagens da comunidade e a {NOME_AGENTE} escreve um post para o LinkedIn, um destaque para a newsletter e uma sugestão de FAQ. "
    "Você edita, aprova e publica com o seu próprio login: nada vai ao ar sem a sua revisão.</p>"
    "<p class='pequeno'>Versão de demonstração, com dados simulados.</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.divider()



def _carregar_lote(origem):
    """Lê as mensagens escolhidas. Devolve (lote, identificador) ou (None, None) com a mensagem na tela."""
    try:
        if origem == "Exemplo do projeto":
            exemplos = exemplos_de_demonstracao()
            if not exemplos:
                st.warning("Não encontrei os exemplos na pasta dados/. Abra a tela na pasta raiz do projeto.")
                return None, None
            caminho, nome = st.selectbox("Exemplo", exemplos, format_func=lambda e: e[1])
            return carregar_lote_de_exemplo(caminho), f"exemplo:{caminho.name}"

        arquivo = st.file_uploader("Arquivo .json ou .csv", type=["json", "csv"])
        if arquivo is None:
            st.info("Envie um arquivo .json ou .csv, ou escolha um exemplo do projeto.")
            return None, None
        return carregar_lote_enviado(arquivo.name, arquivo.getvalue()), f"envio:{arquivo.name}:{arquivo.size}"
    except (ValueError, FileNotFoundError) as erro:
        st.error(f"Não consegui carregar as mensagens.\n\n{erro}")
        return None, None


st.subheader("1. Escolha as mensagens e gere o conteúdo")
origem = st.radio("De onde vêm as mensagens?", ["Exemplo do projeto", "Enviar arquivo"], horizontal=True)
col_escolha, col_botao = st.columns([3, 1], vertical_alignment="bottom")
with col_escolha:
    lote, identificador = _carregar_lote(origem)

if lote is None:
    st.stop()

with col_botao:
    gerar = st.button("Gerar conteúdo", type="primary", width="stretch")

st.info(frase_do_lote(lote))

with st.expander("Conferir o que a comunidade escreveu", expanded=False):
    st.caption("Confira se são as mensagens certas e, depois, compare com os textos gerados.")
    st.dataframe(tabela_de_mensagens(lote), width="stretch", hide_index=True)

autores = autores_do_lote(lote)
with st.expander("Alguém não autorizou a divulgação do nome?", expanded=False):
    st.caption(
        "Marque quem não autorizou. Antes de gerar, o nome dessa pessoa é trocado por “uma pessoa da comunidade” "
        "nas mensagens, e o agente conta a história sem identificá-la. "
        "Apelidos, cargos e outros detalhes ainda podem identificar alguém: confira o texto mesmo assim."
    )
    sem_autorizacao = st.multiselect("Não tenho autorização para divulgar o nome de:", autores, key=f"sem_aut:{identificador}")
if sem_autorizacao:
    st.caption("Ao gerar, os nomes marcados serão trocados antes de o texto ir ao agente.")


def _limpar_revisao():
    """Novo conteúdo gerado: some com as edições e as decisões do conteúdo anterior."""
    for chave in [k for k in st.session_state if str(k).startswith(("campo:", "conf_"))]:
        del st.session_state[chave]
    st.session_state["decisoes"] = {}


if gerar:
    try:
        with st.spinner("Gerando o conteúdo..."):
            lote_para_gerar, trocas = anonimizar_pessoas(lote, sem_autorizacao)
            st.session_state["resultado"] = executar(lote_para_gerar)
            st.session_state["resultado_de"] = identificador
            st.session_state["trocas"] = trocas
            _limpar_revisao()
    except (ValueError, FileNotFoundError, ErroServicoLLM) as erro:
        st.session_state.pop("resultado", None)
        st.session_state.pop("trocas", None)
        st.error(f"Não consegui gerar o conteúdo.\n\n{erro}")

resultado = st.session_state.get("resultado")
if resultado is None or st.session_state.get("resultado_de") != identificador:
    st.stop()

resposta = resultado.resposta
st.session_state.setdefault("decisoes", {})
resumo = resposta["resumo_comunidade"]

st.divider()
st.subheader("Conteúdos prontos para revisar")
st.warning(
    f"**⚠️ A {NOME_AGENTE} é uma inteligência artificial e pode cometer erros.** Antes de publicar, confira duas coisas:\n\n"
    "1. **Os fatos**, comparando com o que a comunidade escreveu.\n"
    "2. **A autorização de quem aparece com nome** nos textos.\n\n"
    "O texto também pode mudar a cada vez que você gerar."
)
for troca in st.session_state.get("trocas", []):
    m, c = troca["mensagens"], troca["citacoes"]
    partes = [f"{m} mensagem dela" if m == 1 else f"{m} mensagens dela"]
    if c:
        partes.append(f"{c} citação nas mensagens" if c == 1 else f"{c} citações nas mensagens")
    aviso = (
        f"**Nome trocado antes de gerar:** {troca['pessoa']} → “{troca['rotulo']}” ({' e '.join(partes)}). "
        "Confira mesmo assim se o texto ainda identifica alguém."
    )
    if troca["so_nome_completo"]:
        aviso += " O primeiro nome também é de outra pessoa do lote, então só o nome completo foi trocado."
    st.info(aviso)


def _hora(registro):
    return datetime.fromisoformat(registro["data_hora"]).strftime("%d/%m às %H:%M")


def _voltar_ao_original(chave, original):
    for campo, valor in original.items():
        st.session_state[f"campo:{chave}:{campo}"] = valor


@st.dialog("Confirmar aprovação")
def _confirmar_aprovacao(chave, nome_ativo, original, atuais, pessoas):
    st.markdown(f"Você vai aprovar: **{nome_ativo}**.")
    if pessoas:
        st.markdown("Pessoas citadas no texto: **" + ", ".join(pessoas) + "**")
        st.info(
            "**Sem a autorização delas?** Feche esta janela e faça uma de duas coisas:\n\n"
            f"- **Edite o texto** e tire o nome, por exemplo trocando por “{EXEMPLO_SEM_NOME}”. Depois, aprove de novo.\n"
            "- Ou **marque a pessoa** em “Alguém não autorizou a divulgação do nome?” (no começo da página) e gere de novo.\n"
            "- Ou **reprove** o texto, com o motivo “Sem autorização das pessoas citadas”."
        )
    else:
        st.caption("Não encontrei nome de pessoa no texto. Se houver algum, confira mesmo assim.")
    fatos = st.checkbox("Conferi os fatos, comparando com o que a comunidade escreveu.", key=f"conf_fatos:{chave}")
    autorizacao = st.checkbox(
        ("Tenho a autorização de " + ", ".join(pessoas) + " para publicar o nome.") if pessoas
        else "Conferi que o texto não traz o nome de ninguém sem autorização.",
        key=f"conf_autorizacao:{chave}",
    )
    if st.button("Confirmar aprovação", type="primary", disabled=not (fatos and autorizacao), width="stretch"):
        _guardar(registrar_decisao(chave, "aprovado", st.session_state.get("revisor", ""), original, atuais, pessoas,
                                   conferiu_fatos=fatos, conferiu_autorizacao=autorizacao))
        st.rerun()


@st.dialog("Reprovar texto")
def _confirmar_reprovacao(chave, nome_ativo, original, atuais, pessoas):
    st.markdown(f"Você vai reprovar: **{nome_ativo}**. Ele não entra nos textos aprovados.")
    opcao = st.selectbox("Motivo (opcional)", MOTIVOS_REPROVACAO, index=None, placeholder="Escolha um motivo", key=f"conf_motivo:{chave}")
    detalhe = st.text_input("Detalhe (opcional)", key=f"conf_detalhe:{chave}", placeholder="Ex.: pediram para não aparecer")
    if pessoas and opcao is None:
        st.caption("Dica: se o problema é a falta de autorização, escolha “Sem autorização das pessoas citadas”.")
    motivo = montar_motivo(opcao, detalhe)
    if st.button("Confirmar reprovação", type="primary", width="stretch"):
        _guardar(registrar_decisao(chave, "reprovado", st.session_state.get("revisor", ""), original, atuais, pessoas, motivo=motivo))
        st.rerun()


def _guardar(registro):
    """Guarda a decisão na tela e grava o estado em saida/ (nunca envia ao OCI)."""
    st.session_state["decisoes"][registro["ativo"]] = registro
    salvar_decisoes(st.session_state["decisoes"], lote["periodo_referencia"])
    for chave in [k for k in st.session_state if str(k).startswith("conf_") and str(k).endswith(registro["ativo"])]:
        del st.session_state[chave]


def _cartao(ativo, caracteres_por_linha):
    """Desenha um conteúdo gerado (post, destaque ou FAQ) dentro de um cartão: editar, aprovar ou reprovar."""
    with st.container(border=True):
        # Etiqueta amarela com texto preto (só o nome fixo do cartão entra no HTML, nunca texto de usuário)
        st.markdown(f"<span class='etiqueta'>{ativo['nome']}</span>", unsafe_allow_html=True)
        if not ativo["existe"]:
            st.caption(ativo["sem_material"])
            return
        chave = ativo["chave"]
        original = texto_do_ativo(resposta, chave)
        campo_do_rotulo = {rotulo: campo for campo, rotulo in campos_editaveis(chave)}
        for rotulo, valor in ativo["campos"]:
            if rotulo in campo_do_rotulo:
                campo = campo_do_rotulo[rotulo]
                chave_campo = f"campo:{chave}:{campo}"
                st.session_state.setdefault(chave_campo, valor)
                # Altura pelo tamanho do texto atual: o quadro mostra tudo, sem cortar o final (quem edita vê a altura se ajustar)
                altura = altura_do_campo(st.session_state[chave_campo], caracteres_por_linha)
                st.text_area(rotulo, key=chave_campo, height=altura)
            else:
                st.markdown(f"**{rotulo}:** {valor}")
        atuais = {campo: st.session_state[f"campo:{chave}:{campo}"] for campo in original}

        if atuais != original:
            st.caption("✏️ Você alterou este texto.")
            st.button("Voltar ao texto gerado", key=f"voltar:{chave}", on_click=_voltar_ao_original, args=(chave, original))
        pessoas = pessoas_citadas_no_ativo(atuais, lote)
        st.caption("Pessoas citadas neste texto: " + (", ".join(pessoas) if pessoas else "nenhuma encontrada."))
        if pessoas:
            st.caption(f"Sem a autorização delas? Troque o nome no texto (por exemplo, por “{EXEMPLO_SEM_NOME}”), marque quem não autorizou no começo da página e gere de novo, ou reprove.")

        decisao = st.session_state["decisoes"].get(chave)
        if decisao and decisao_vale(decisao, atuais):
            if decisao["decisao"] == "aprovado":
                st.success(f"✅ Aprovado por {decisao['revisor']} em {_hora(decisao)}")
            else:
                st.error(f"❌ Reprovado por {decisao['revisor']} em {_hora(decisao)}" + (f". Motivo: {decisao['motivo']}" if decisao["motivo"] else ""))
        elif decisao:
            st.warning(f"Você alterou o texto depois de {'aprovar' if decisao['decisao'] == 'aprovado' else 'reprovar'}. Aprove ou reprove de novo.")
        else:
            st.caption("Aguardando a sua revisão.")

        # Os botões ficam sempre ligados: desligados sem avisar, parecem quebrados. Sem nome, a tela explica o que fazer.
        pode = nome_do_revisor_valido(st.session_state.get("revisor", ""))
        b1, b2 = st.columns(2)
        clicou = False
        if b1.button("Aprovar", key=f"aprovar:{chave}", type="primary", width="stretch"):
            clicou = True
            if pode:
                _confirmar_aprovacao(chave, ativo["nome"], original, atuais, pessoas)
        if b2.button("Reprovar", key=f"reprovar:{chave}", width="stretch"):
            clicou = True
            if pode:
                _confirmar_reprovacao(chave, ativo["nome"], original, atuais, pessoas)
        if clicou and not pode:
            st.error("Antes de decidir, escreva o seu nome no campo “Seu nome (quem está revisando)”, no começo desta área, e aperte **Enter**. Depois clique de novo.")

        origens = resultado.origens.get(chave, [])
        with st.expander(f"De quais mensagens pode ter vindo ({len(origens)})"):
            st.caption(
                "Mensagens analisadas cujo tipo alimenta este texto. "
                "O agente não registra qual mensagem gerou qual trecho."
            )
            for m in origens:
                st.markdown(f"- **{m['autor']}** · {m['canal']} · `{m['tipo']}`" + (f" · {m['id']}" if m["id"] else ""))


st.text_input("Seu nome (quem está revisando)", key="revisor", placeholder="Ex.: Maria Silva")
st.caption(
    "O nome é **declarado por você, sem login**: nesta versão de demonstração a tela não confirma quem é a pessoa. "
    "Ele aparece no registro de cada aprovação ou reprovação. Depois de escrever, aperte **Enter**."
)

# O post (o mais comprido) fica à esquerda; o destaque da newsletter e a FAQ ficam empilhados à direita
post, destaque, faq = ativos_para_exibir(resposta)
coluna_post, coluna_outros = st.columns([3, 2])
with coluna_post:
    _cartao(post, caracteres_por_linha=95)
with coluna_outros:
    _cartao(destaque, caracteres_por_linha=48)
    _cartao(faq, caracteres_por_linha=48)

# Quantos textos já foram revisados e o arquivo para baixar
st.divider()
st.markdown("#### Revisão")
existentes = [a for a in (post, destaque, faq) if a["existe"]]
validas = {}
for a in existentes:
    d = st.session_state["decisoes"].get(a["chave"])
    atuais = {campo: st.session_state.get(f"campo:{a['chave']}:{campo}") for campo in texto_do_ativo(resposta, a["chave"])}
    if d and decisao_vale(d, atuais):
        validas[a["chave"]] = d
aprovados = sum(1 for d in validas.values() if d["decisao"] == "aprovado")
reprovados = sum(1 for d in validas.values() if d["decisao"] == "reprovado")
st.markdown(f"**{aprovados}** aprovado(s) · **{reprovados}** reprovado(s) · **{len(existentes) - len(validas)}** aguardando revisão")
aprovados_agora = [d for d in validas.values() if d["decisao"] == "aprovado"]
if aprovados_agora:
    st.markdown("#### Prontos para publicar")
    st.caption(
        "**1. Copie** o texto (ícone no canto do quadro). **2. Abra** o LinkedIn e **cole**. "
        f"Quem publica entra com o próprio login: a {NOME_AGENTE} não publica nada sozinha."
    )
    for d in aprovados_agora:
        st.markdown(f"**{ATIVOS[d['ativo']][0]}**")
        st.code(texto_para_publicar(d["ativo"], d["texto_final"]), language=None, wrap_lines=True)
        if d["ativo"] == "post_linkedin":
            st.link_button("Abrir o LinkedIn (depois, cole o texto)", URL_LINKEDIN)

with st.expander("Para o time técnico"):
    if validas:
        st.caption(f"O registro da revisão foi salvo neste computador em `{caminho_curadoria(lote['periodo_referencia'])}`. Nada foi enviado ao OCI.")
    st.download_button(
        "Baixar os textos aprovados (.json)",
        data=json.dumps(pacote_aprovado(validas, lote["periodo_referencia"]), ensure_ascii=False, indent=2),
        file_name=f"{lote['periodo_referencia']}_textos-aprovados.json",
        mime="application/json",
        disabled=aprovados == 0,
    )

st.divider()
st.markdown("#### Resumo da comunidade")
r1, r2, r3 = st.columns([1, 2, 3])
r1.caption("Mensagens analisadas")
r1.markdown(f"**{resumo['total_interacoes_processadas']}**")
r2.caption("Clima da comunidade")
r2.markdown(f"**{clima_da_comunidade(resumo['sentimento_predominante'])}**")
r3.caption("Assuntos da semana")
r3.markdown("**" + ", ".join(resumo["topicos_principais"]) + "**")
for aviso in resultado.avisos:
    st.info(aviso)
