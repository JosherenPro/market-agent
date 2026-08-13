"""Interface Streamlit pour l'agent marché public (Togo).

Style inspiré de la plateforme officielle service-public.gouv.tg :
vert institutionnel, or national, fonds clairs, cartes et hiérarchie claire.
"""

import requests
from langchain_core.messages import AIMessageChunk, ToolMessage

import rag
import streamlit as st
from agent import agent
from tools import indexer_marches

st.set_page_config(
    page_title="Agent Marchés Publics Togo",
    page_icon=":material/account_balance:",
    layout="wide",
)

st.markdown(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">',
    unsafe_allow_html=True,
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

:root {
    /* Palette réelle du portail service-public.gouv.tg (thème NIMBLE) */
    --green:        #43a842;   /* vert principal (boutons, login) */
    --green-hover:  #3a9439;
    --green-900:    #006a4f;   /* fin du dégradé hero / bas sidebar */
    --blue:         #116E9B;   /* bleu (liens, icônes, survols) */
    --teal-nav:     #026B58;   /* onglet Citoyens actif */
    --grad-begin:   #116e9b;   /* début dégradé hero */
    --grad-end:     #006a4f;   /* fin dégradé hero */
    --gold:         #EAC802;   /* bannière d'alerte */
    --gold-deep:    #D9B400;
    --orange:       #EA7F02;
    --red:          #D11135;
    --green-100:    #E7F8E7;
    --white:        #FFFFFF;
    --bg:          #F6F8FA;   /* fond gris clair */
    --nav-grey:     #ebeff4;
    --ink:          #212529;
    --ink-soft:     #6b7280;
    --line:         #e5e5e5;
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.07);
    --shadow-lg: 0 10px 34px rgba(0, 0, 0, 0.12);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;
    --font-body: 'Poppins', -apple-system, 'Segoe UI', sans-serif;
    --font-heading: 'Poppins', -apple-system, 'Segoe UI', sans-serif;
    --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] li, [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] span, [data-testid="stExpander"] summary, [data-testid="stExpander"] p, [data-testid="stMetric"] label, [data-testid="stMetric"] div, .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span, .stMarkdown li, .stMarkdown strong, .stMarkdown em {
    color: var(--ink) !important;
    font-family: var(--font-body);
    background-color: transparent;
}

.stApp {
    background: linear-gradient(180deg, var(--white) 0%, var(--bg) 460px);
}

[data-testid="stHeader"] { background: transparent; }
#MainMenu { visibility: hidden; }
[data-testid="stFooter"] { display: none; }
/* Keep the sidebar collapse/expand chevron usable so it can be reopened */
[data-testid="stToolbar"] { display: block !important; }

/* ---------- National bar ---------- */
.flag-bar {
    display: flex; height: 4px; border-radius: 2px; overflow: hidden;
    margin: 0 0 18px;
}
.flag-bar span { flex: 1; }
.flag-bar span:nth-child(1) { background: var(--green-900); }
.flag-bar span:nth-child(2) { background: var(--gold); }
.flag-bar span:nth-child(3) { background: var(--red); }

/* ---------- Hero ---------- */
.hero {
    background: linear-gradient(270deg, var(--grad-begin) -23%, var(--grad-end) 100%);
    border-radius: var(--radius-lg);
    padding: 36px 40px 40px;
    margin: 0 0 26px;
    box-shadow: var(--shadow-lg);
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(500px 200px at 12% -20%, rgba(255, 209, 0, 0.18), transparent 60%),
        radial-gradient(600px 260px at 90% 120%, rgba(255, 255, 255, 0.07), transparent 60%);
}
.hero__emblem {
    width: 64px; height: 64px; margin: 0 auto 14px;
    background: var(--white);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    box-shadow: var(--shadow-md);
    font-family: var(--font-heading); font-weight: 800; font-size: 24px;
    color: var(--green-900);
    border: 3px solid var(--gold);
    position: relative;
}
.hero__kicker {
    font-size: 11px; font-weight: 700; letter-spacing: 2.8px;
    text-transform: uppercase; color: var(--gold);
    margin-bottom: 8px;
}
.hero__title {
    font-family: var(--font-heading);
    font-size: 34px; font-weight: 800;
    color: var(--white); margin: 0 0 10px; letter-spacing: -0.4px;
    position: relative;
}
.hero__sub {
    color: rgba(255, 255, 255, 0.85);
    font-size: 15px; max-width: 620px; margin: 0 auto 18px;
    line-height: 1.6; position: relative;
}
.hero__chips { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; position: relative; }
.chip {
    font-size: 11.5px; font-weight: 600; padding: 6px 14px; border-radius: 999px;
    letter-spacing: 0.3px;
}
.chip--gold { background: var(--gold); color: var(--green-900); font-weight: 700; }
.chip--ghost { background: rgba(255, 255, 255, 0.10); color: rgba(255, 255, 255, 0.9); border: 1px solid rgba(255, 255, 255, 0.22); }

/* ---------- Pillars (3 blocks) ---------- */
.pillar {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 22px 20px;
    box-shadow: var(--shadow-sm);
    height: 100%;
    transition: var(--transition);
    border-top: 4px solid transparent;
}
.pillar:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-top-color: var(--blue);
}
.pillar__icon {
    width: 42px; height: 42px; border-radius: 10px;
    background: var(--green-100); color: var(--blue);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; margin-bottom: 12px;
}
.pillar__title {
    font-family: var(--font-heading); font-weight: 700; font-size: 15px;
    color: var(--ink); margin: 0 0 6px;
}
.pillar__text { font-size: 12.5px; color: var(--ink-soft); line-height: 1.55; margin: 0; }

/* ---------- Section title ---------- */
.section-title {
    font-family: var(--font-heading);
    font-size: 15px; font-weight: 700; color: var(--ink);
    padding: 0 0 10px; margin: 0;
    border-bottom: 2px solid var(--blue);
    display: inline-block;
    text-transform: uppercase; letter-spacing: 0.6px;
}

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] {
    max-width: 880px;
    margin-left: auto; margin-right: auto;
}
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    border-radius: var(--radius-sm);
    font-size: 14px;
}
[data-testid="stChatMessageAvatarUser"] {
    background: var(--gold);
    color: var(--green-900);
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: var(--green-900);
    color: var(--white);
}
[data-testid="stChatMessageContent"] {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: 14px 18px;
    box-shadow: var(--shadow-sm);
    line-height: 1.65;
}
[data-testid="stChatMessageContent"] p:last-child { margin-bottom: 0; }

/* Empty-state welcome + suggestion chips */
.chat-welcome {
    max-width: 880px; margin: 0 auto 14px; text-align: center;
}
.chat-welcome__title {
    font-family: var(--font-heading); font-weight: 700; font-size: 1.25rem;
    color: var(--green-900); margin: 0 0 6px;
}
.chat-welcome__sub { color: var(--ink-soft); font-size: .95rem; margin: 0 0 16px; }
/* Suggestion buttons become white cards with blue left border (main area only) */
button[data-testid="stBaseButton-secondary"] {
    display: block !important; text-align: left !important; width: 100% !important;
    background: var(--white) !important; color: var(--ink) !important;
    border: 1px solid var(--line) !important; border-left: 4px solid var(--blue) !important;
    border-radius: var(--radius-sm) !important; padding: 12px 14px !important;
    font-size: .9rem !important; font-weight: 500 !important;
    box-shadow: var(--shadow-sm) !important; transition: var(--transition) !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--blue) !important; border-left-color: var(--blue) !important;
    box-shadow: var(--shadow-md) !important; transform: translateY(-2px) !important;
}

/* Tool blocks inside the expander */
.tool-block {
    background: var(--bg);
    border: 1px solid var(--line);
    border-left: 3px solid var(--green-900);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 13px;
    color: var(--ink);
}
.tool-block__name {
    font-family: 'SFMono-Regular', 'Cascadia Mono', Consolas, monospace;
    font-weight: 700; font-size: 12px; letter-spacing: .4px;
    color: var(--green-900);
    margin-bottom: 4px;
}
.tool-block__content { color: var(--ink-soft); white-space: pre-wrap; }

[data-testid="stExpander"] {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}
[data-testid="stExpander"] summary { font-weight: 600; color: var(--ink); }

/* ---------- Chat input ---------- */
[data-testid="stChatInput"] { max-width: 880px; margin-left: auto; margin-right: auto; }
[data-testid="stChatInput"] textarea {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--line) !important;
    background: var(--white) !important;
    box-shadow: var(--shadow-sm);
    font-size: 1rem !important;
    padding: 14px 16px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #6b7280 !important; opacity: 1 !important; font-size: .95rem;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--green) !important;
    box-shadow: 0 0 0 3px rgba(67, 168, 66, 0.18) !important;
}
[data-testid="stChatInput"] button {
    background: var(--green) !important;
    border-radius: var(--radius-sm) !important;
    width: 52px !important; height: 52px !important;
    transition: background var(--transition);
}
[data-testid="stChatInput"] button:hover { background: var(--green-hover) !important; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--grad-begin) 0%, var(--grad-end) 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] * { color: #EDF5F1 !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: rgba(237, 245, 241, 0.6) !important; }
.side-brand {
    display: flex; align-items: center; gap: 12px;
    padding: 6px 0 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 2px;
}
.side-brand__logo {
    width: 38px; height: 38px; border-radius: 50%;
    background: var(--white);
    border: 2px solid var(--gold);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--font-heading); font-weight: 800; font-size: 15px;
    color: var(--green-900);
}
.side-brand__title { font-family: var(--font-heading); font-weight: 700; font-size: 15px; }
.side-brand__sub { font-size: 11.5px; color: rgba(237, 245, 241, 0.55); }
.side-title {
    font-size: 11px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase;
    color: var(--gold) !important;
    border-bottom: 1px solid rgba(255, 209, 0, 0.3);
    padding-bottom: 8px; margin: 22px 0 12px;
}
[data-testid="stSidebar"] .stButton button {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: var(--radius-sm);
    font-weight: 600;
    color: #EDF5F1;
    transition: var(--transition);
    width: 100%;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: var(--gold);
    color: var(--gold);
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] {
    background: var(--gold);
    border: none;
    color: var(--green-900);
    font-weight: 700;
}
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"]:hover {
    background: #FFE033;
    color: var(--green-900);
}
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: #EDF5F1;
}

/* ---------- Footer ---------- */
.footer {
    text-align: center; color: var(--ink-soft); font-size: 12px; margin: 36px 0 10px;
    border-top: 1px solid var(--line); padding-top: 16px;
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def ollama_alive() -> bool:
    try:
        return requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def refresh_rag_count() -> int:
    try:
        return rag.get_vectorstore()._collection.count()
    except Exception:
        return 0


def hero_html() -> str:
    return """
    <div class="flag-bar"><span></span><span></span><span></span></div>
    <div class="hero">
        <div class="hero__emblem">MP</div>
        <div class="hero__kicker">République togolaise · Service public</div>
        <h1 class="hero__title">Agent Marchés Publics</h1>
        <p class="hero__sub">Assistant de veille des appels d'offres, avis et consultations
        publiés sur le portail officiel des marchés publics du Togo.</p>
        <div class="hero__chips">
            <span class="chip chip--gold">gemma4 · Ollama</span>
            <span class="chip chip--ghost">Tavily Search</span>
            <span class="chip chip--ghost">RAG · ChromaDB</span>
        </div>
    </div>
    """


def pillar_html(icon: str, title: str, text: str) -> str:
    return f"""
    <div class="pillar">
        <div class="pillar__icon">{icon}</div>
        <div class="pillar__title">{title}</div>
        <div class="pillar__text">{text}</div>
    </div>
    """


st.markdown(hero_html(), unsafe_allow_html=True)

alive = ollama_alive()
rag_count = refresh_rag_count()

c1, c2, c3 = st.columns(3, vertical_alignment="center")
c1.markdown(pillar_html('<i class="bi bi-person-fill"></i>', "Citoyens", "Suivez les consultations ouvertes, les avis d'appel d'offres et les délais de dépôt."), unsafe_allow_html=True)
c2.markdown(pillar_html('<i class="bi bi-buildings"></i>', "Entreprises", "Identifiez les marchés par secteur — BTP, fournitures, services, informatique."), unsafe_allow_html=True)
c3.markdown(pillar_html('<i class="bi bi-bank2"></i>', "Professionnels", "Interrogez la base RAG : pièces requises, organismes, montants, procédures."), unsafe_allow_html=True)

st.markdown(
    '<div style="margin:28px 0 14px;"><span class="section-title">Base RAG</span></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-brand__logo">MP</div>
            <div>
                <div class="side-brand__title">Agent Marchés</div>
                <div class="side-brand__sub">Service public du Togo</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-title">Base RAG</div>', unsafe_allow_html=True)
    if st.button("Indexer les offres du portail", key="btn_index", type="primary", width="stretch"):
        with st.spinner("Scraping du portail et indexation en cours..."):
            result = indexer_marches.invoke({})
        st.success(result)
        st.rerun()

    if st.button("Vider la base RAG", key="btn_clear", width="stretch"):
        n = rag.clear_index()
        st.warning(f"{n} documents supprimés.")
        st.rerun()

    st.markdown('<div class="side-title">Conversation</div>', unsafe_allow_html=True)
    if st.button("Nouvelle conversation", key="btn_new", width="stretch"):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="side-title">Recherches sauvegardées</div>', unsafe_allow_html=True)
    if "saved_searches" not in st.session_state:
        st.session_state.saved_searches = []
    if not st.session_state.saved_searches:
        st.markdown(
            '<div style="font-size:12px;color:rgba(237,245,241,0.5);">Aucune recherche sauvegardée pour l\'instant.</div>',
            unsafe_allow_html=True,
        )
    else:
        for s_idx, s_txt in enumerate(st.session_state.saved_searches):
            col_a, col_b = st.columns([5, 1])
            with col_a:
                if st.button(f"🔍 {s_txt[:38]}{'…' if len(s_txt) > 38 else ''}",
                             key=f"load_{s_idx}", width="stretch"):
                    st.session_state.messages.append({"role": "user", "content": s_txt})
                    st.rerun()
            with col_b:
                if st.button("✕", key=f"del_{s_idx}", help="Supprimer"):
                    st.session_state.saved_searches.pop(s_idx)
                    st.rerun()

    st.markdown('<div class="side-title">Exemples</div>', unsafe_allow_html=True)
    st.markdown(
        """
        - *"Quels sont les appels d'offres récents ?"*
        - *"Y a-t-il des marchés BTP ouverts ?"*
        - *"Cherche le web : réglementation 2026"*
        - *"Quelles pièces sont requises pour soumissionner ?"*
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="position:sticky;bottom:0;padding-top:10px;font-size:11px;color:rgba(237,245,241,0.4);">
            Données : marches-publics-togo.com<br>
            Généré localement avec gemma4
        </div>
        """,
        unsafe_allow_html=True,
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

SUGGESTIONS = [
    ("bi bi-megaphone", "Quels sont les appels d'offres récents ?"),
    ("bi bi-building", "Y a-t-il des marchés BTP ouverts ?"),
    ("bi bi-globe", "Cherche le web : réglementation 2026"),
    ("bi bi-clipboard-check", "Quelles pièces pour soumissionner ?"),
]


def tool_block(name: str, content: str) -> str:
    return f"""
    <div class="tool-block">
        <div class="tool-block__name">{name}</div>
        <div class="tool-block__content">{content[:400]}</div>
    </div>
    """


def render_history() -> None:
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(
            "user" if role == "user" else "assistant",
            avatar=":material/person:" if role == "user" else ":material/account_balance:",
        ):
            if role == "tool":
                st.markdown(tool_block(msg["name"], msg["content"]), unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])


render_history()

# Empty state: welcome + clickable suggestion chips
if not st.session_state.messages:
    st.markdown(
        """
        <div class="chat-welcome">
            <div class="chat-welcome__title">Comment puis-je vous aider ?</div>
            <div class="chat-welcome__sub">Posez une question ou choisissez un exemple pour démarrer votre veille des marchés publics.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (icon, label) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(
                label,
                key=f"suggest_{i}",
                use_container_width=True,
                help=f"Exemple : {label}",
            ):
                st.session_state.messages.append({"role": "user", "content": label})
                st.rerun()


def run_agent(prompt: str) -> None:
    """Exécute l'agent sur une question et affiche la réponse + le bouton de sauvegarde."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    history = [
        (m["role"], m["content"])
        for m in st.session_state.messages
        if m["role"] in {"user", "assistant"}
    ]

    with st.chat_message("assistant", avatar=":material/account_balance:"):
        tools_box = st.expander("Outils utilisés", expanded=False)
        text_placeholder = st.empty()
        answer = ""
        config = {"recursion_limit": 25}

        for chunk, metadata in agent.stream(
            {"messages": history}, config=config, stream_mode="messages"
        ):
            node = metadata.get("langgraph_node")
            if node == "tools" and isinstance(chunk, ToolMessage):
                tools_box.markdown(
                    tool_block(chunk.name, chunk.content), unsafe_allow_html=True
                )
            elif node == "agent" and isinstance(chunk, AIMessageChunk):
                if chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        tools_box.markdown(
                            tool_block(tc["name"], "Appel de l'outil en cours..."),
                            unsafe_allow_html=True,
                        )
                elif chunk.content:
                    answer += chunk.content
                    text_placeholder.markdown(answer + "▌")

        if answer:
            text_placeholder.markdown(answer)
        else:
            text_placeholder.markdown("_(aucune réponse générée)_")

    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        if st.button(
            "💾 Sauvegarder cette recherche",
            key=f"save_{len(st.session_state.messages)}",
            type="primary",
            width="stretch",
        ):
            if prompt and prompt not in st.session_state.saved_searches:
                st.session_state.saved_searches.append(prompt)
            st.rerun()


if prompt := st.chat_input("Posez une question sur les marchés publics..."):
    run_agent(prompt)

st.markdown(
    '<div class="footer">Agent Marchés Publics Togo · service-public.gouv.tg · LangGraph · LangChain · ChromaDB · Tavily · Ollama</div>',
    unsafe_allow_html=True,
)