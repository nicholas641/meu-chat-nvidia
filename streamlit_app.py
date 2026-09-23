"""
Aether Engine — Chat IA
-----------------------
Chat normal com IA. Raciocinio visivel em expander colapsavel.
"""

import os
import pickle
import urllib.parse
from datetime import datetime
import uuid

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ============================================================
# PERSISTENCIA
# ============================================================
def salvar_historico_no_disco():
    try:
        with open("backup_chat.pkl", "wb") as f:
            pickle.dump(st.session_state.messages, f)
    except Exception:
        pass


def carregar_historico_do_disco():
    if os.path.exists("backup_chat.pkl"):
        try:
            with open("backup_chat.pkl", "rb") as f:
                return pickle.load(f)
        except Exception:
            return []
    return []


# ============================================================
# API KEY
# ============================================================
def _load_api_key() -> str:
    try:
        if "NVIDIA_API_KEY" in st.secrets:
            return st.secrets["NVIDIA_API_KEY"]
    except Exception:
        pass
    key = os.getenv("NVIDIA_API_KEY")
    if key:
        return key
    st.error(
        "Chave de API nao configurada. Defina NVIDIA_API_KEY em "
        "st.secrets ou como variavel de ambiente."
    )
    st.stop()


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=_load_api_key(),
)
MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


# ============================================================
# AVATARES INVISIVEIS
# ============================================================
_SVG_USER = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
    'data-id="useravatar"><circle cx="20" cy="20" r="20" fill="none"/></svg>'
)
_SVG_AI = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
    'data-id="aiavatar"><circle cx="20" cy="20" r="20" fill="none"/></svg>'
)
_AVATAR_USER = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(_SVG_USER)
_AVATAR_AI   = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(_SVG_AI)


# ============================================================
# ICONES SVG
# ============================================================
def _svg(path: str, size: int = 18) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{path}</svg>'
    )

ICON_PLUS    = _svg('<path d="M12 5v14M5 12h14"/>', 16)
ICON_FOLDER  = _svg('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>', 16)
ICON_HISTORY = _svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 16)
ICON_GEAR    = _svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>', 16)
ICON_REFRESH = _svg('<path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/>', 15)
ICON_MIC     = _svg('<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/>', 18)
ICON_TRASH   = _svg('<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>', 16)
ICON_EDIT    = _svg('<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z"/>', 15)
ICON_STOP    = _svg('<rect x="6" y="6" width="12" height="12" rx="2"/>', 14)
ICON_STAR    = _svg('<polygon points="12 2 15 9 22 9.3 16.5 14 18.5 21 12 17 5.5 21 7.5 14 2 9.3 9 9"/>', 14)
ICON_ARROWL  = _svg('<path d="M19 12H5M12 19l-7-7 7-7"/>', 15)
ICON_BRAIN   = _svg('<path d="M9.5 2a3.5 3.5 0 0 0-3.5 3.5v.5A3 3 0 0 0 4 9v1a3 3 0 0 0 1 2.2V15a4 4 0 0 0 4 4h.5V2H9.5z"/><path d="M14.5 2a3.5 3.5 0 0 1 3.5 3.5v.5A3 3 0 0 1 20 9v1a3 3 0 0 1-1 2.2V15a4 4 0 0 1-4 4h-.5V2h.5z"/>', 15)


# ============================================================
# SYSTEM PROMPT — assistente normal
# ============================================================
BASE_SYSTEM_PROMPT = """You are Aether, a helpful, friendly AI assistant.

- Respond naturally and conversationally, in the same language the user
  writes in.
- Be direct and useful. No need to be overly formal.
- When the user asks for code, provide the code in a normal fenced
  markdown block (```lang ... ```). Do NOT wrap it in special tags like
  <artifact> unless the user explicitly asks for that.
- Never invent tools, artifacts, preview panels, or capabilities you do
  not have. You are a chat assistant.
- Keep reasoning concise and useful; do not pad with filler.
"""


def build_system_prompt() -> str:
    prompt = BASE_SYSTEM_PROMPT
    custom = (st.session_state.get("custom_instructions") or "").strip()
    if custom:
        prompt += (
            "\n\nUser personalization instructions (ALWAYS follow these):\n"
            + custom
        )
    return prompt


# ============================================================
# PAGE CONFIG
# ============================================================
_FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%23c96442'/%3E"
    "%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' "
    "fill='%23ffffff' text-anchor='middle'%3EA%3C/text%3E%3C/svg%3E"
)

st.set_page_config(
    page_title="Aether Engine",
    page_icon=_FAVICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================
_DEFAULTS = {
    "messages":            carregar_historico_do_disco(),
    "pending_prompt":      None,
    "temperature":         1.0,
    "top_p":               0.95,
    "max_tokens":          8192,
    "attached_name":       None,
    "attached_text":       None,
    "editing_idx":         None,
    "stop_requested":      False,
    "search_query":        "",
    "custom_instructions": "",
    "conversations":       [],
    "show_history":        False,
    "show_projects":       False,
    "show_settings":       False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# HELPERS DE CONVERSA
# ============================================================
def _reset_conversation():
    st.session_state.messages = []
    st.session_state.editing_idx = None


def _close_panels():
    st.session_state.show_history = False
    st.session_state.show_projects = False
    st.session_state.show_settings = False


def _snapshot_conversation(pinned: bool = False, title: str = None):
    if not st.session_state.messages:
        return
    if title is None:
        first_user = next(
            (m["content"] for m in st.session_state.messages if m["role"] == "user"),
            "Conversa",
        )
        title = (first_user or "Conversa").strip().splitlines()[0][:42]
    st.session_state.conversations.insert(0, {
        "id":       str(uuid.uuid4())[:8],
        "title":    title or "Conversa sem titulo",
        "ts":       datetime.now().strftime("%d/%m %H:%M"),
        "messages": st.session_state.messages,
        "pinned":   pinned,
    })


def _load_conversation(conv_id: str) -> bool:
    for c in st.session_state.conversations:
        if c["id"] == conv_id:
            st.session_state.messages = c.get("messages", [])
            st.session_state.editing_idx = None
            return True
    return False


# ============================================================
# QUERY PARAM ROUTER
# ============================================================
_action = st.query_params.get("a")
_idx_qp = st.query_params.get("i")
if _action:
    st.query_params.clear()

    if _action == "new":
        _snapshot_conversation(pinned=False)
        _reset_conversation()
        _close_panels()
        st.toast("Nova conversa iniciada", icon=":material/check_circle:")

    elif _action == "mic":
        st.toast(
            "Gravacao de audio nao esta disponivel neste ambiente.",
            icon=":material/mic_off:",
        )

    elif _action == "projects":
        st.session_state.show_projects = not st.session_state.show_projects
        st.session_state.show_history = False
        st.session_state.show_settings = False

    elif _action == "history":
        st.session_state.show_history = not st.session_state.show_history
        st.session_state.show_projects = False
        st.session_state.show_settings = False

    elif _action == "settings":
        st.session_state.show_settings = not st.session_state.show_settings
        st.session_state.show_history = False
        st.session_state.show_projects = False

    elif _action == "close_panel":
        _close_panels()

    elif _action == "load_conv" and _idx_qp is not None:
        _loaded = _load_conversation(_idx_qp)
        _close_panels()
        if _loaded:
            st.toast("Conversa carregada", icon=":material/history:")

    elif _action == "toggle_pin_conv" and _idx_qp is not None:
        for c in st.session_state.conversations:
            if c["id"] == _idx_qp:
                c["pinned"] = not c["pinned"]
                break

    elif _action == "delete_conv" and _idx_qp is not None:
        st.session_state.conversations = [
            c for c in st.session_state.conversations if c["id"] != _idx_qp
        ]

    elif _action == "clear_attach":
        st.session_state.attached_name = None
        st.session_state.attached_text = None
        st.toast("Anexo removido", icon=":material/delete:")

    elif _action == "clear_chat":
        st.session_state.messages = []
        if os.path.exists("backup_chat.pkl"):
            try:
                os.remove("backup_chat.pkl")
            except Exception:
                pass
        st.rerun()

    elif _action == "stop_generation":
        st.session_state.stop_requested = True

    elif _action == "cancel_edit":
        st.session_state.editing_idx = None

    elif _action == "edit" and _idx_qp is not None:
        try:
            st.session_state.editing_idx = int(_idx_qp)
        except ValueError:
            st.session_state.editing_idx = None

    elif _action == "regen":
        msgs = st.session_state.messages
        if msgs and msgs[-1]["role"] == "assistant":
            msgs.pop()
        if msgs and msgs[-1]["role"] == "user":
            last_user = msgs.pop()
            st.session_state.pending_prompt = last_user["content"]
        st.rerun()


# ============================================================
# CSS
# ============================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    :root, html, body { color-scheme: light !important; }
    :root {
        --background-color: #fafaf7 !important;
        --text-color: #1f1e1c !important;
        --secondary-background-color: #ffffff !important;
        --primary-color: #c96442 !important;
    }
    :root {
        --bg:           #fafaf7;
        --bg-2:         #f5f4ee;
        --card:         #ffffff;
        --panel:        #f1efe8;
        --bg-user:      #edeae0;
        --bg-code:      #f5f4ee;
        --bg-think:     #fbf8f3;
        --border:       #e6e3d8;
        --border-soft:  #efecdf;
        --text:         #1f1e1c;
        --text-dim:     #66635b;
        --text-mute:    #9a978e;
        --accent:       #c96442;
        --accent-hover: #b85738;
        --shadow-sm:    0 1px 2px rgba(0,0,0,.03);
        --shadow-md:    0 4px 14px rgba(0,0,0,.06);
        --radius-sm:    8px;
        --radius-md:    12px;
        --radius-lg:    18px;
    }

    #MainMenu { visibility: hidden; }
    footer { display: none !important; visibility: hidden; }
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"],
    .stDeployButton,
    [data-testid="stAppDeployButton"] { display: none !important; }
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        background: transparent !important;
    }

    [data-testid="InputInstructions"],
    [data-testid="stFormSubmitButton"] + small,
    [data-testid="stTextInput"] + small,
    [data-testid="stTextInputRootElement"] + small,
    .stForm small {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important; width: 0 !important; opacity: 0 !important;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                     "Segoe UI", Roboto, sans-serif !important;
        color: var(--text);
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
    }
    .block-container {
        padding: 0.6rem 1.4rem 1rem 1.4rem !important;
        max-width: 100% !important;
    }

    /* FIX INPUT ESCURO */
    input, textarea, [contenteditable],
    [data-testid="stTextInput"],
    [data-testid="stTextInput"] > div,
    [data-testid="stTextInput"] > div > div,
    [data-testid="stTextInputRootElement"],
    [data-testid="stTextArea"],
    [data-testid="stTextArea"] > div,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="input"],
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"],
    [data-baseweb="textarea"],
    [data-baseweb="base-input"] input,
    [data-baseweb="textarea"] textarea,
    .stTextInput input,
    .stTextArea textarea,
    section[data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        color: #1f1e1c !important;
        -webkit-text-fill-color: #1f1e1c !important;
        caret-color: #c96442 !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"],
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] > div,
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] > div > div,
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-baseweb="input"],
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-baseweb="base-input"],
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] input {
        background-color: transparent !important;
    }
    input::placeholder, textarea::placeholder,
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="textarea"] textarea::placeholder {
        color: #9a978e !important;
        -webkit-text-fill-color: #9a978e !important;
        opacity: 1 !important;
    }
    [data-testid="stForm"], [data-testid="stSidebarContent"] {
        background-color: #ffffff !important;
    }

    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stMarkdown div, .stMarkdown strong, .stMarkdown em, .stMarkdown a,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] * {
        color: var(--text) !important;
    }
    .stMarkdown code, [data-testid="stMarkdownContainer"] code {
        color: var(--text) !important;
        background: var(--bg-code) !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        width: 248px !important;
        min-width: 248px !important;
        max-width: 248px !important;
        background-color: var(--bg-2) !important;
        border-right: 1px solid var(--border-soft) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.9rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.15rem !important;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] button,
    button[kind="header"] { display: none !important; }

    section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
        font-size: 13px !important;
        height: 34px !important;
        padding: 4px 12px !important;
        background: #ffffff !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
    }

    .sb-brand {
        display: flex; align-items: center; gap: 10px;
        padding: 4px 2px 14px 2px; margin-bottom: 6px;
    }
    .sb-brand-mark {
        width: 30px; height: 30px;
        background: var(--accent); color: #ffffff;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Lora', Georgia, serif;
        font-size: 16px; font-weight: 500; flex-shrink: 0;
    }
    .sb-brand-info { display: flex; flex-direction: column; line-height: 1.15; }
    .sb-brand-name { font-size: 14px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
    .sb-brand-tag  { font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.02em; }

    .sb-section {
        font-size: 10.5px; font-weight: 600;
        color: var(--text-mute); letter-spacing: 0.1em;
        text-transform: uppercase; padding: 16px 8px 6px 8px;
    }

    .sb-btn {
        display: flex !important; align-items: center; gap: 10px;
        padding: 8px 10px; margin: 1px 0;
        border-radius: var(--radius-sm);
        color: var(--text-dim) !important;
        font-size: 13.5px; font-weight: 500;
        text-decoration: none !important;
        transition: background-color 0.15s ease, color 0.15s ease;
        cursor: pointer; line-height: 1.2;
    }
    .sb-btn:hover { background: rgba(0,0,0,.04); color: var(--text) !important; }
    .sb-btn svg { flex-shrink: 0; opacity: 0.7; }
    .sb-btn:hover svg { opacity: 1; }
    .sb-btn span { color: inherit; }
    .sb-btn.active { background: rgba(201,100,66,.08); color: var(--accent) !important; }
    .sb-btn.active svg { opacity: 1; }

    .sb-btn-primary {
        background: var(--accent); color: #ffffff !important;
        box-shadow: 0 1px 2px rgba(201,100,66,.2); margin-bottom: 4px;
        font-weight: 600;
    }
    .sb-btn-primary:hover { background: var(--accent-hover); color: #ffffff !important; }
    .sb-btn-primary svg { opacity: 1; }

    /* HEADER */
    .app-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 4px 6px 12px 6px;
        background: transparent; border: none; margin-bottom: 6px;
        max-width: 800px; margin-left: auto; margin-right: auto;
    }
    .app-header-left { display: flex; align-items: center; gap: 10px; }
    .app-brand-info { line-height: 1.15; }
    .app-brand-name {
        font-family: 'Lora', Georgia, serif;
        font-size: 17px; font-weight: 500;
        color: var(--text); letter-spacing: -0.01em;
    }
    .app-brand-tag  { font-size: 11px; color: var(--text-mute); margin-top: 1px; }
    .app-status {
        display: inline-flex; align-items: center; gap: 7px;
        padding: 4px 10px;
        background: transparent;
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        font-size: 11.5px; font-weight: 500;
        color: var(--text-dim);
    }
    .app-status-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #6ba944;
        box-shadow: 0 0 0 3px rgba(107,169,68,.15);
    }

    /* CHAT */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important; border-radius: 0 !important;
        padding: 4px 0 !important; margin-bottom: 22px !important;
        box-shadow: none !important;
        display: flex !important; flex-direction: row !important;
        align-items: flex-start !important; gap: 0 !important;
        animation: fadeUp 0.28s cubic-bezier(0.16, 1, 0.3, 1);
        max-width: 800px !important;
        margin-left: auto !important; margin-right: auto !important;
    }
    [data-testid="stChatMessage"] img {
        display: none !important; width: 0 !important; height: 0 !important;
    }
    [data-testid="stChatMessageContent"] {
        flex: 1 1 auto !important;
        max-width: 100% !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important; border-radius: 0 !important;
    }

    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) {
        flex-direction: row-reverse !important;
        margin: 4px auto 26px auto !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-user) !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 10px 16px !important;
        max-width: 78% !important; flex: 0 1 auto !important;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li {
        color: var(--text) !important;
        font-size: 15px; line-height: 1.75;
    }
    [data-testid="stChatMessage"] p { margin-bottom: 12px; }
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3 {
        font-family: 'Lora', Georgia, serif;
        font-weight: 500;
        letter-spacing: -0.01em;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(3px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* RACIOCINIO */
    [data-testid="stChatMessage"] [data-testid="stExpander"] {
        border: 1px solid var(--border-soft) !important;
        background: var(--bg-think) !important;
        border-radius: var(--radius-md) !important;
        margin: 0 0 16px 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        transition: border-color 0.15s ease;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"]:hover {
        border-color: var(--border) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] details {
        border: none !important; background: transparent !important; padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary {
        padding: 10px 14px !important;
        color: var(--text-dim) !important;
        list-style: none !important;
        font-weight: 500 !important;
        font-size: 12.5px !important;
        background: transparent !important;
        display: flex !important; align-items: center !important;
        transition: color 0.15s ease, background-color 0.15s ease;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary:hover {
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary p {
        font-size: 12.5px !important; color: inherit !important;
        display: inline !important; margin: 0 !important;
        letter-spacing: 0.02em;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary svg {
        width: 12px !important; height: 12px !important;
        opacity: 0.6; margin-right: 8px;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {
        border: none !important;
        border-top: 1px solid var(--border-soft) !important;
        padding: 14px 18px !important;
        margin: 0 !important;
        background: transparent !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] p,
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] li {
        font-size: 13.5px !important;
        color: var(--text-dim) !important;
        line-height: 1.75 !important;
        opacity: 1 !important;
    }

    .think-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 10px; margin-bottom: 8px;
        background: rgba(201,100,66,.08);
        border: 1px solid rgba(201,100,66,.2);
        border-radius: 999px;
        font-size: 10.5px; font-weight: 700;
        color: var(--accent) !important;
        letter-spacing: 0.1em; text-transform: uppercase;
    }

    .msg-actions {
        display: flex; gap: 14px; align-items: center;
        margin-top: 10px; opacity: 0;
        transition: opacity 0.15s ease;
    }
    [data-testid="stChatMessage"]:hover .msg-actions { opacity: 1; }
    .msg-action {
        font-size: 11.5px;
        color: var(--text-mute) !important;
        text-decoration: none !important;
        cursor: pointer; font-weight: 500;
        display: inline-flex; align-items: center; gap: 4px;
        transition: color 0.15s ease;
    }
    .msg-action:hover { color: var(--accent) !important; }

    /* EDIT FORM */
    [data-testid="stChatMessage"] [data-testid="stForm"] {
        background: var(--card) !important;
        border: 1px solid var(--accent) !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 12px !important; margin-top: 6px !important;
    }
    [data-testid="stTextArea"] textarea {
        font-size: 14px !important; line-height: 1.55 !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 12px !important;
        background: var(--bg) !important;
    }

    /* CODE */
    [data-testid="stChatMessage"] [data-testid="stCode"],
    [data-testid="stChatMessage"] pre,
    .stCodeBlock pre {
        background: #f7f6f1 !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
    }
    [data-testid="stChatMessage"] pre code,
    [data-testid="stChatMessage"] [data-testid="stCode"] code,
    .stCodeBlock code {
        background: transparent !important;
        color: var(--text) !important;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace !important;
        font-size: 13px !important; line-height: 1.65 !important;
    }

    /* CURSOR */
    .cursor {
        display: inline-block;
        width: 7px; height: 1.05em;
        background: var(--accent);
        vertical-align: text-bottom;
        margin-left: 3px;
        border-radius: 1px;
        animation: blink 1s step-start infinite;
        opacity: 0.85;
    }
    @keyframes blink { 50% { opacity: 0.15; } }

    .thinking-dots {
        display: inline-flex; gap: 4px; align-items: center;
        margin-left: 6px; vertical-align: middle;
    }
    .thinking-dots span {
        width: 5px; height: 5px; border-radius: 50%;
        background: var(--accent);
        animation: bounce 1.2s infinite ease-in-out;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.15s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
        40% { transform: translateY(-4px); opacity: 1; }
    }

    /* COMPOSER */
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 24px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,.06) !important;
        margin: 12px auto 0 auto;
        max-width: 800px;
        padding: 6px 8px !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) > div > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stHorizontalBlock"] {
        align-items: center !important; gap: 4px !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] > div {
        border: none !important; background: transparent !important; box-shadow: none !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] input {
        background: transparent !important;
        border: none !important;
        color: #1f1e1c !important;
        -webkit-text-fill-color: #1f1e1c !important;
        caret-color: var(--accent) !important;
        font-size: 15px !important;
        padding: 12px 10px !important;
        height: 48px !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stTextInput"] input::placeholder {
        color: var(--text-mute) !important;
        -webkit-text-fill-color: var(--text-mute) !important;
        opacity: 1 !important;
    }

    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stPopover"] > button {
        width: 42px !important; height: 42px !important; min-width: 42px !important;
        padding: 0 !important; font-size: 0 !important; color: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        box-shadow: none !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='19' height='19' viewBox='0 0 24 24' fill='none' stroke='%239a978e' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        transition: background-color 0.15s ease !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stPopover"] > button:hover {
        background-color: var(--panel) !important;
    }

    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 50% !important;
        width: 42px !important; height: 42px !important; min-width: 42px !important;
        padding: 0 !important; font-size: 0 !important;
        box-shadow: 0 1px 2px rgba(201,100,66,.25) !important;
        transition: background-color 0.15s ease, transform 0.15s ease !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 19V5M5 12l7-7 7 7'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether..."]) [data-testid="stFormSubmitButton"] button:hover {
        background-color: var(--accent-hover) !important;
        transform: translateY(-1px);
    }

    .composer-mic {
        width: 42px !important; height: 42px !important;
        display: inline-flex !important;
        align-items: center !important; justify-content: center !important;
        color: var(--text-mute) !important;
        border: none !important;
        border-radius: 50% !important;
        text-decoration: none !important; background: transparent;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .composer-mic:hover {
        color: var(--accent) !important;
        background: var(--panel);
        text-decoration: none !important;
    }

    .attach-chip {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 12px;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        font-size: 12px;
        color: var(--text-dim) !important;
        margin: 4px auto 6px auto;
        max-width: 800px;
    }
    .attach-chip span { color: var(--text-dim) !important; }
    .attach-chip a {
        color: var(--text-mute) !important;
        text-decoration: none; font-weight: 600;
        margin-left: 4px; transition: color 0.15s ease;
    }
    .attach-chip a:hover { color: var(--accent) !important; }

    .stop-wrap {
        display: flex; justify-content: center;
        margin: 8px auto 12px auto;
        max-width: 800px;
    }
    .stop-wrap a {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 7px 14px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 999px;
        font-size: 12px; font-weight: 500;
        color: var(--text-dim) !important;
        text-decoration: none !important;
        box-shadow: var(--shadow-sm);
        transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease;
    }
    .stop-wrap a:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.04);
    }

    /* EMPTY */
    .empty-hero {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        padding: 60px 20px 40px 20px;
        max-width: 600px; margin: 0 auto;
    }
    .empty-hero-mark {
        width: 52px; height: 52px;
        background: var(--accent); color: #ffffff;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Lora', Georgia, serif;
        font-size: 26px; font-weight: 500;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(201,100,66,.25);
    }
    .empty-hero-title {
        font-family: 'Lora', Georgia, serif;
        font-size: 26px; font-weight: 500;
        color: var(--text) !important;
        margin-bottom: 10px; letter-spacing: -0.02em;
    }
    .empty-hero-sub {
        font-size: 14px;
        color: var(--text-mute) !important;
        line-height: 1.6;
    }

    /* PAINEIS */
    .panel-title {
        font-family: 'Lora', Georgia, serif;
        font-size: 20px; font-weight: 500;
        color: var(--text);
        max-width: 800px; margin: 0 auto 8px auto;
        padding: 8px 4px;
    }
    .hist-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 10px;
        border-bottom: 1px solid var(--border-soft);
        gap: 8px;
        border-radius: var(--radius-sm);
        transition: background-color 0.15s ease;
        max-width: 800px; margin: 0 auto;
    }
    .hist-row:hover { background: rgba(0,0,0,.02); }
    .hist-row-main { flex: 1 1 auto; min-width: 0; text-decoration: none !important; }
    .hist-title {
        font-size: 14px; font-weight: 500; color: var(--text) !important;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .hist-meta { font-size: 11.5px; color: var(--text-mute) !important; margin-top: 2px; }
    .hist-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
    .hist-action {
        color: var(--text-mute) !important; text-decoration: none !important;
        display: inline-flex; align-items: center; cursor: pointer;
        transition: color 0.15s ease;
    }
    .hist-action:hover { color: var(--accent) !important; }
    .hist-action.pinned { color: var(--accent) !important; }
    .panel-empty {
        padding: 60px 20px; text-align: center;
        color: var(--text-mute); font-size: 13.5px; line-height: 1.7;
        max-width: 500px; margin: 0 auto;
    }
    .panel-back {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 12.5px; font-weight: 500;
        color: var(--text-dim) !important;
        text-decoration: none !important;
        margin: 0 auto 12px auto;
        max-width: 800px;
        transition: color 0.15s ease;
    }
    .panel-back:hover { color: var(--accent) !important; }
    .settings-hint {
        font-size: 13px; color: var(--text-mute) !important;
        line-height: 1.65; margin-bottom: 12px;
    }
    .settings-section {
        font-size: 11px; font-weight: 600; color: var(--text-mute);
        letter-spacing: 0.08em; text-transform: uppercase;
        margin: 18px 0 10px 0;
    }

    /* BOTOES GENERICOS */
    .stButton > button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.5rem 1rem !important;
        transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease !important;
        box-shadow: none !important; cursor: pointer !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    .stButton > button:focus { box-shadow: none !important; outline: none !important; }
    .stButton > button p { color: inherit !important; margin: 0 !important; }

    [data-testid="stFormSubmitButton"] button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        box-shadow: none !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    [data-testid="stFormSubmitButton"] button p { color: inherit !important; margin: 0 !important; }

    [data-testid="stPopover"] > button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stPopoverBody"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-md) !important;
        color: var(--text) !important;
    }
    [data-testid="stPopoverBody"] * { color: var(--text) !important; }

    [data-testid="stFileUploader"] section {
        background: var(--panel) !important;
        border: 1px dashed var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stFileUploader"] section * { color: var(--text) !important; }
    [data-testid="stFileUploader"] section button {
        background: var(--card) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
    }

    .stAlert {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
        background: var(--panel) !important;
        color: var(--text) !important;
        max-width: 800px;
        margin-left: auto; margin-right: auto;
    }
    .stAlert * { color: var(--text) !important; }

    [data-testid="stToast"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text) !important;
        box-shadow: var(--shadow-md) !important;
    }
    [data-testid="stToast"] * { color: var(--text) !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #d9d5c8; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #c9c4b3; }

    /* MOBILE */
    [data-testid="stSidebarNav"] { display: none !important; }

    @media (max-width: 900px) {
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        button[kind="header"],
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        [data-testid="collapsedControl"] {
            background: var(--card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: var(--shadow-sm) !important;
            color: var(--accent) !important;
            top: 12px !important; left: 12px !important;
        }
        section[data-testid="stSidebar"] {
            width: 240px !important; min-width: 240px !important; max-width: 240px !important;
            box-shadow: 2px 0 18px rgba(0,0,0,.08);
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            margin-left: -240px !important;
            transition: margin-left 0.2s ease;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            transition: margin-left 0.2s ease;
        }
        .app-header { padding: 4px 4px 10px 52px !important; }
        .app-brand-tag { display: none; }
    }

    @media (max-width: 640px) {
        .block-container { padding: 0.4rem 0.9rem 0.6rem 0.9rem !important; }
        .app-brand-name { font-size: 15px; }
        .app-status { padding: 4px 8px; font-size: 11px; }
        .empty-hero-title { font-size: 22px; }
        .empty-hero { padding: 40px 16px 20px 16px; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# ATALHO ESC
# ============================================================
components.html(
    """
    <script>
    (function () {
        const doc = window.parent.document;
        if (doc.__aetherEscBound) return;
        doc.__aetherEscBound = true;
        doc.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            const url = new URL(window.parent.location.href);
            if (url.searchParams.get('a') === 'edit') {
                url.searchParams.set('a', 'cancel_edit');
                url.searchParams.delete('i');
                window.parent.location.href = url.toString();
            }
        });
    })();
    </script>
    """,
    height=0,
)


# ============================================================
# SIDEBAR
# ============================================================
_cls_proj = "sb-btn active" if st.session_state.show_projects else "sb-btn"
_cls_hist = "sb-btn active" if st.session_state.show_history else "sb-btn"
_cls_conf = "sb-btn active" if st.session_state.show_settings else "sb-btn"

with st.sidebar:
    st.markdown(f"""
    <div class="sb-brand">
        <div class="sb-brand-mark">A</div>
        <div class="sb-brand-info">
            <div class="sb-brand-name">Aether</div>
            <div class="sb-brand-tag">Chat</div>
        </div>
    </div>

    <a class="sb-btn sb-btn-primary" href="?a=new" target="_self">
        {ICON_PLUS}<span>Nova conversa</span>
    </a>

    <div class="sb-section">Espaco</div>
    <a class="{_cls_proj}" href="?a=projects" target="_self">
        {ICON_FOLDER}<span>Projetos</span>
    </a>
    <a class="{_cls_hist}" href="?a=history" target="_self">
        {ICON_HISTORY}<span>Historico</span>
    </a>

    <div class="sb-section">Sistema</div>
    <a class="{_cls_conf}" href="?a=settings" target="_self">
        {ICON_GEAR}<span>Configuracoes</span>
    </a>
    <a class="sb-btn" href="?a=clear_chat" target="_self">
        {ICON_TRASH}<span>Limpar conversa</span>
    </a>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Busca</div>', unsafe_allow_html=True)
    _search_input = st.text_input(
        "Buscar na conversa",
        placeholder="Filtrar mensagens...",
        label_visibility="collapsed",
        key="sidebar_search",
    )
    st.session_state.search_query = _search_input or ""


# ============================================================
# APP HEADER
# ============================================================
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <div class="app-brand-info">
            <div class="app-brand-name">Aether</div>
            <div class="app-brand-tag">Assistente conversacional</div>
        </div>
    </div>
    <div class="app-status">
        <span class="app-status-dot"></span>
        <span>Online</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# PAINEIS
# ============================================================
def _hist_row_html(c: dict, show_pin: bool = True) -> str:
    pin_cls = "hist-action pinned" if c.get("pinned") else "hist-action"
    pin_title = "Remover dos projetos" if c.get("pinned") else "Salvar como projeto"
    pin_html = (
        f'<a class="{pin_cls}" href="?a=toggle_pin_conv&i={c["id"]}" '
        f'target="_self" title="{pin_title}">{ICON_STAR}</a>'
        if show_pin else ""
    )
    return f"""
    <div class="hist-row">
        <a class="hist-row-main" href="?a=load_conv&i={c['id']}" target="_self">
            <div class="hist-title">{c['title']}</div>
            <div class="hist-meta">{c['ts']} · {len(c.get('messages', []))} mensagens</div>
        </a>
        <div class="hist-actions">
            {pin_html}
            <a class="hist-action" href="?a=delete_conv&i={c['id']}" target="_self" title="Excluir">{ICON_TRASH}</a>
        </div>
    </div>
    """


def _render_settings_panel():
    st.markdown(
        f'<a class="panel-back" href="?a=close_panel" target="_self">'
        f'{ICON_ARROWL}<span>Voltar para a conversa</span></a>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="panel-title">Configuracoes</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="settings-hint" style="max-width:800px;margin:0 auto 12px auto;">'
        'Escreva como voce quer que o Aether responda (tom, girias, '
        'regras fixas). Isso e enviado junto de toda mensagem, como '
        'uma memoria persistente da conversa.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form("settings_form", clear_on_submit=False):
        custom = st.text_area(
            "Personalizacao",
            value=st.session_state.custom_instructions,
            placeholder="Ex: seja informal, use girias brasileiras, va direto ao ponto...",
            height=140,
            label_visibility="collapsed",
        )
        st.markdown(
            '<div class="settings-section">Geracao</div>',
            unsafe_allow_html=True,
        )
        temp = st.slider(
            "Criatividade (temperature)",
            0.0, 2.0, float(st.session_state.temperature), 0.05,
        )
        topp = st.slider(
            "Top P", 0.0, 1.0, float(st.session_state.top_p), 0.05,
        )
        saved = st.form_submit_button(
            "Salvar configuracoes", use_container_width=True,
        )
        if saved:
            st.session_state.custom_instructions = custom.strip()
            st.session_state.temperature = temp
            st.session_state.top_p = topp
            st.toast("Configuracoes salvas", icon=":material/check_circle:")


def _render_history_panel():
    st.markdown(
        f'<a class="panel-back" href="?a=close_panel" target="_self">'
        f'{ICON_ARROWL}<span>Voltar para a conversa</span></a>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="panel-title">Historico</div>', unsafe_allow_html=True)
    if not st.session_state.conversations:
        st.markdown(
            '<div class="panel-empty">Nenhuma conversa salva ainda.<br>'
            'Conversas anteriores aparecem aqui quando voce clica em '
            '"Nova conversa".</div>',
            unsafe_allow_html=True,
        )
    else:
        for c in st.session_state.conversations:
            st.markdown(_hist_row_html(c), unsafe_allow_html=True)


def _render_projects_panel():
    st.markdown(
        f'<a class="panel-back" href="?a=close_panel" target="_self">'
        f'{ICON_ARROWL}<span>Voltar para a conversa</span></a>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="panel-title">Projetos</div>', unsafe_allow_html=True)

    if st.session_state.messages:
        default_title = next(
            (m["content"] for m in st.session_state.messages if m["role"] == "user"),
            "Meu projeto",
        )
        with st.form("save_project_form", clear_on_submit=True):
            name = st.text_input(
                "Nome do projeto",
                value=(default_title or "Meu projeto").strip().splitlines()[0][:42],
            )
            saved = st.form_submit_button(
                "Salvar conversa atual como projeto", use_container_width=True,
            )
            if saved:
                _snapshot_conversation(pinned=True, title=name.strip() or "Projeto")
                st.toast("Projeto salvo", icon=":material/bookmark:")

    pinned = [c for c in st.session_state.conversations if c.get("pinned")]
    if not pinned:
        st.markdown(
            '<div class="panel-empty" style="padding-top:30px;">'
            'Nenhum projeto salvo ainda.<br>'
            'Salve a conversa atual acima, ou marque uma conversa do '
            'historico com a estrela.</div>',
            unsafe_allow_html=True,
        )
    else:
        for c in pinned:
            st.markdown(_hist_row_html(c), unsafe_allow_html=True)


# ============================================================
# PAINEL ATIVO
# ============================================================
_panel_active = (
    st.session_state.show_settings
    or st.session_state.show_history
    or st.session_state.show_projects
)

if _panel_active:
    if st.session_state.show_settings:
        _render_settings_panel()
    elif st.session_state.show_history:
        _render_history_panel()
    elif st.session_state.show_projects:
        _render_projects_panel()
    st.stop()


# ============================================================
# CHAT
# ============================================================
_do_rerun = False

_prompt = st.session_state.pending_prompt
st.session_state.pending_prompt = None

if _prompt:
    if st.session_state.attached_text:
        _prompt = (
            f"{_prompt}\n\n"
            f"[Arquivo anexado: {st.session_state.attached_name}]\n"
            f"```\n{st.session_state.attached_text[:4000]}\n```"
        )
    st.session_state.messages.append({"role": "user", "content": _prompt})
    salvar_historico_no_disco()

_query = (st.session_state.search_query or "").strip().lower()


# ---- Mensagens ----
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-hero">
        <div class="empty-hero-mark">A</div>
        <div class="empty-hero-title">Como posso ajudar hoje?</div>
        <div class="empty-hero-sub">
            Pergunte qualquer coisa, bata um papo, peca uma ideia ou codigo.<br>
            O raciocinio do modelo aparece em tempo real durante a resposta.
        </div>
    </div>
    """, unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    if _query and _query not in (msg.get("content") or "").lower():
        continue

    if msg["role"] == "user":
        with st.chat_message("user", avatar=_AVATAR_USER):
            if st.session_state.editing_idx == i:
                with st.form(f"edit_form_{i}", clear_on_submit=False):
                    st.markdown(
                        '<div style="font-size:11px;font-weight:600;'
                        'color:#c96442;letter-spacing:.08em;'
                        'text-transform:uppercase;margin-bottom:6px;">'
                        'Editando mensagem'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    new_text = st.text_area(
                        "Editar",
                        value=msg["content"],
                        key=f"edit_area_{i}",
                        label_visibility="collapsed",
                        height=130,
                    )
                    cc1, cc2 = st.columns([1.4, 1])
                    with cc1:
                        save = st.form_submit_button(
                            "Salvar e reenviar", use_container_width=True,
                        )
                    with cc2:
                        cancel = st.form_submit_button(
                            "Cancelar", use_container_width=True,
                        )
                    if save and new_text.strip():
                        st.session_state.messages = st.session_state.messages[:i]
                        st.session_state.pending_prompt = new_text.strip()
                        st.session_state.editing_idx = None
                        st.rerun()
                    if cancel:
                        st.session_state.editing_idx = None
                        st.rerun()
            else:
                st.markdown(msg["content"])
                st.markdown(
                    f'<div class="msg-actions">'
                    f'<a class="msg-action" href="?a=edit&i={i}" target="_self">'
                    f'{ICON_EDIT}<span>editar</span></a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        with st.chat_message("assistant", avatar=_AVATAR_AI):
            if msg.get("thinking"):
                with st.expander("Raciocinio do modelo"):
                    st.markdown(
                        f'<div class="think-badge">{ICON_BRAIN}<span>Aether pensou</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["thinking"])
            if msg.get("content"):
                st.markdown(msg["content"])
            is_last = (i == len(st.session_state.messages) - 1)
            if is_last:
                st.markdown(
                    f'<div class="msg-actions">'
                    f'<a class="msg-action" href="?a=regen" target="_self">'
                    f'{ICON_REFRESH}<span>regenerar</span></a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ---- Streaming ----
if _prompt:
    with st.chat_message("assistant", avatar=_AVATAR_AI):

        stop_holder = st.empty()
        with stop_holder:
            st.markdown(
                f'<div class="stop-wrap">'
                f'<a href="?a=stop_generation" target="_self">'
                f'{ICON_STOP}<span>Parar geracao</span></a>'
                f'</div>',
                unsafe_allow_html=True,
            )

        thinking_slot = st.expander("Raciocinio do modelo", expanded=True)
        with thinking_slot:
            st.markdown(
                f'<div class="think-badge">{ICON_BRAIN}<span>Aether pensou</span></div>',
                unsafe_allow_html=True,
            )
            thinking_body = st.empty()
            thinking_body.markdown(
                '<span class="thinking-dots"><span></span><span></span><span></span></span>',
                unsafe_allow_html=True,
            )

        text_body = st.empty()

        raw_buffer = ""
        reasoning_accum = ""

        try:
            api_messages = (
                [{"role": "system", "content": build_system_prompt()}]
                + st.session_state.messages
            )

            completion = client.chat.completions.create(
                model=MODEL,
                messages=api_messages,
                temperature=st.session_state.temperature,
                top_p=st.session_state.top_p,
                max_tokens=st.session_state.max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}},
                stream=True,
            )

            for chunk in completion:
                if st.session_state.get("stop_requested"):
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    reasoning_accum += reasoning
                    thinking_body.markdown(
                        reasoning_accum + '<span class="cursor"></span>',
                        unsafe_allow_html=True,
                    )

                if delta.content:
                    raw_buffer += delta.content
                    text_body.markdown(
                        raw_buffer + '<span class="cursor"></span>',
                        unsafe_allow_html=True,
                    )

            stop_holder.empty()

            if not reasoning_accum:
                with thinking_slot:
                    thinking_body.markdown("_Sem raciocinio exposto._")

            text_body.markdown(raw_buffer or "_Sem resposta._")

            st.session_state.messages.append({
                "role":     "assistant",
                "content":  raw_buffer,
                "thinking": reasoning_accum,
            })
            salvar_historico_no_disco()

        except Exception as e:
            st.error(f"Falha ao processar resposta: {e}")
            st.session_state.messages.append({
                "role":     "assistant",
                "content":  f"Erro: {e}",
                "thinking": "",
            })
            salvar_historico_no_disco()

    st.session_state.stop_requested = False
    st.session_state.attached_name = None
    st.session_state.attached_text = None
    _do_rerun = True


# ---- Anexo ----
if st.session_state.attached_name:
    st.markdown(
        f'<div class="attach-chip">'
        f'<span>{st.session_state.attached_name}</span>'
        f'<a href="?a=clear_attach" target="_self" title="Remover">remover</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---- Composer ----
with st.form("composer", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(
        [0.35, 6, 0.35, 0.7],
        gap="small",
        vertical_alignment="center",
    )
    with c1:
        with st.popover("Anexar", use_container_width=False):
            uploaded = st.file_uploader(
                "Anexar arquivo",
                type=["txt", "md", "py", "js", "html", "css", "json"],
                label_visibility="collapsed",
            )
            if uploaded is not None:
                try:
                    st.session_state.attached_name = uploaded.name
                    st.session_state.attached_text = uploaded.read().decode(
                        "utf-8", errors="ignore"
                    )
                    st.success(f"Anexado: {uploaded.name}")
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")

    with c2:
        user_msg = st.text_input(
            "mensagem",
            placeholder="Envie uma mensagem para o Aether...",
            label_visibility="collapsed",
        )
    with c3:
        st.markdown(
            f'<a class="composer-mic" href="?a=mic" target="_self" '
            f'title="Gravar audio">{ICON_MIC}</a>',
            unsafe_allow_html=True,
        )
    with c4:
        submitted = st.form_submit_button("Enviar")

if submitted and user_msg.strip():
    st.session_state.pending_prompt = user_msg.strip()
    st.rerun()


# ============================================================
# RERUN
# ============================================================
if _do_rerun:
    st.rerun()
