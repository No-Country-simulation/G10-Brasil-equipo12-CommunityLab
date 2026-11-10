# interface_streamlit.py
"""Interface de curadoria do CommunityLab (passo 1: gerar o conteúdo; passo 2: editar, aprovar ou reprovar cada texto).

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
    ATIVOS,
    URL_LINKEDIN,
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

# Depois da votação, troque só o nome aqui. Para o mascote, salve a imagem em assets/mascote.png.
NOME_AGENTE = "CommunityLab"
MASCOTE = Path("assets/mascote.png")

st.set_page_config(page_title=f"{NOME_AGENTE} · Curadoria", page_icon=str(MASCOTE) if MASCOTE.is_file() else "🧪", layout="wide", initial_sidebar_state="collapsed")

if MASCOTE.is_file():
    col_mascote, col_titulo = st.columns([1, 8], vertical_alignment="center")
    col_mascote.image(str(MASCOTE), width=90)
    col_titulo.title(NOME_AGENTE)
else:
    st.title(f"🧪 {NOME_AGENTE}")

st.markdown(f"### {NOME_AGENTE} transforma o que a sua comunidade conta em conteúdo pronto para publicar.")
st.markdown("Você escolhe as mensagens, o agente entende sozinho o que cada uma pode virar e entrega um post, um destaque de newsletter e uma sugestão de FAQ para você revisar.")
st.caption("Versão de demonstração, com dados simulados.")

# Etiqueta amarela com texto preto (cores da marca) e largura máxima da página. As demais cores ficam em .streamlit/config.toml.
st.markdown(
    "<style>"
    ".etiqueta{background:#FFD966;color:#111111;font-weight:700;padding:4px 14px;border-radius:999px;display:inline-block;}"
    # Em tela larga, as linhas de texto ficariam compridas demais: limita e centraliza a página
    "[data-testid='stMainBlockContainer'],.block-container{max-width:1500px;margin-left:auto;margin-right:auto;}"
    "</style>",
    unsafe_allow_html=True,
)



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

def _limpar_revisao():
    """Novo conteúdo gerado: some com as edições e as decisões do conteúdo anterior."""
    for chave in [k for k in st.session_state if str(k).startswith(("campo:", "conf_"))]:
        del st.session_state[chave]
    st.session_state["decisoes"] = {}


if gerar:
    try:
        with st.spinner("Gerando o conteúdo..."):
            st.session_state["resultado"] = executar(lote)
            st.session_state["resultado_de"] = identificador
            _limpar_revisao()
    except (ValueError, FileNotFoundError, ErroServicoLLM) as erro:
        st.session_state.pop("resultado", None)
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
    f"**⚠️ {NOME_AGENTE} é uma IA e pode cometer erros.** Antes de publicar, confira duas coisas:\n\n"
    "1. **Os fatos**, comparando com o que a comunidade escreveu.\n"
    "2. **A autorização de quem aparece com nome** nos textos.\n\n"
    "O texto também pode mudar a cada vez que você gerar."
)
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


def _cartao(ativo):
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
                altura = 260 if campo == "copy" else (130 if campo == "resumo" else 68)
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
            st.caption(f"Sem a autorização delas? Troque o nome no texto (por exemplo, por “{EXEMPLO_SEM_NOME}”) ou reprove.")

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


st.text_input("Seu nome (quem está revisando)", key="revisor", placeholder="Ex.: Bruna Brandão")
st.caption("O nome aparece no registro de cada aprovação ou reprovação. Depois de escrever, aperte **Enter**.")

# O post (o mais comprido) fica à esquerda; o destaque da newsletter e a FAQ ficam empilhados à direita
post, destaque, faq = ativos_para_exibir(resposta)
coluna_post, coluna_outros = st.columns([3, 2])
with coluna_post:
    _cartao(post)
with coluna_outros:
    _cartao(destaque)
    _cartao(faq)

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
        "Copie o texto (ícone no canto do quadro) e cole onde for publicar. "
        "Quem publica entra com o próprio login: o CommunityLab não publica nada sozinho."
    )
    for d in aprovados_agora:
        st.markdown(f"**{ATIVOS[d['ativo']][0]}**")
        st.code(texto_para_publicar(d["ativo"], d["texto_final"]), language=None, wrap_lines=True)
        if d["ativo"] == "post_linkedin":
            st.link_button("Abrir o LinkedIn", URL_LINKEDIN)

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
