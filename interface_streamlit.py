# interface_streamlit.py
"""Interface de curadoria do CommunityLab (passo 1: carregar mensagens, gerar o conteúdo e mostrar o resultado).

Como abrir (na pasta raiz do projeto, com o ambiente virtual ativo):
    streamlit run interface_streamlit.py

Esta tela NÃO envia nada ao OCI. A lógica fica em src/interface_logica.py (com testes).
A tela é de propósito simples: quem usa só escolhe as mensagens e gera o conteúdo.
"""
from pathlib import Path

import streamlit as st

from src.ia_service import ErroServicoLLM
from src.interface_logica import (
    ativos_para_exibir,
    carregar_lote_de_exemplo,
    carregar_lote_enviado,
    clima_da_comunidade,
    exemplos_de_demonstracao,
    executar,
    frase_do_lote,
    tabela_de_mensagens,
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

if gerar:
    try:
        with st.spinner("Gerando o conteúdo..."):
            st.session_state["resultado"] = executar(lote)
            st.session_state["resultado_de"] = identificador
    except (ValueError, FileNotFoundError, ErroServicoLLM) as erro:
        st.session_state.pop("resultado", None)
        st.error(f"Não consegui gerar o conteúdo.\n\n{erro}")

resultado = st.session_state.get("resultado")
if resultado is None or st.session_state.get("resultado_de") != identificador:
    st.stop()

resposta = resultado.resposta
resumo = resposta["resumo_comunidade"]

st.divider()
st.subheader("Conteúdos prontos para revisar")
st.warning(
    f"**⚠️ {NOME_AGENTE} é uma IA e pode cometer erros.** Antes de publicar, confira duas coisas:\n\n"
    "1. **Os fatos**, comparando com o que a comunidade escreveu.\n"
    "2. **A autorização de quem aparece com nome** nos textos.\n\n"
    "O texto também pode mudar a cada vez que você gerar."
)
def _cartao(ativo):
    """Desenha um conteúdo gerado (post, destaque ou FAQ) dentro de um cartão."""
    with st.container(border=True):
        # Etiqueta amarela com texto preto (só o nome fixo do cartão entra no HTML, nunca texto de usuário)
        st.markdown(f"<span class='etiqueta'>{ativo['nome']}</span>", unsafe_allow_html=True)
        if not ativo["existe"]:
            st.caption(ativo["sem_material"])
            return
        for rotulo, valor in ativo["campos"]:
            if rotulo == "Texto do post":
                # st.code mostra o texto como está (as #hashtags não viram título), com contraste bom e botão de copiar
                st.markdown(f"**{rotulo}:**")
                st.code(valor, language=None, wrap_lines=True)
            else:
                st.markdown(f"**{rotulo}:** {valor}")
        origens = resultado.origens.get(ativo["chave"], [])
        with st.expander(f"De quais mensagens pode ter vindo ({len(origens)})"):
            st.caption(
                "Mensagens analisadas cujo tipo alimenta este texto. "
                "O agente não registra qual mensagem gerou qual trecho."
            )
            for m in origens:
                st.markdown(f"- **{m['autor']}** · {m['canal']} · `{m['tipo']}`" + (f" · {m['id']}" if m["id"] else ""))


# O post (o mais comprido) fica à esquerda; o destaque da newsletter e a FAQ ficam empilhados à direita
post, destaque, faq = ativos_para_exibir(resposta)
coluna_post, coluna_outros = st.columns([3, 2])
with coluna_post:
    _cartao(post)
with coluna_outros:
    _cartao(destaque)
    _cartao(faq)

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
