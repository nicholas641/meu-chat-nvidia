"""
Aether Engine — AI workspace
-----------------------------
Layout: sidebar nativa + header + 2 colunas (chat | preview).
Botao de download do artifact no header do preview.
"""

import os
import re
import urllib.parse
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


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
ICON_IMAGE   = _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>', 44)
ICON_MIC     = _svg('<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/>', 18)
ICON_TRASH   = _svg('<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>', 16)
ICON_DOWNLOAD= _svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>', 14)


# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are Aether Engine, a professional technical assistant.

Strict rules:
1. Never use emojis or emoticons in your responses.
2. Be concise, technical, and direct.
3. Respond in the same language the user writes in.
4. When the user requests a UI component, visual, animation, or HTML/CSS/JS/SVG
   output, wrap the complete code inside <artifact>...</artifact> tags.
   The content must be a full standalone HTML document (with <!DOCTYPE html>).
5. Do not add commentary about the artifact outside the tags beyond a one-line
   summary.
"""


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
    "messages":         [],
    "current_artifact": None,
    "artifact_lang":    None,
    "pending_prompt":   None,
    "temperature":      1.0,
    "top_p":            0.95,
    "max_tokens":       8192,
    "attached_name":    None,
    "attached_text":    None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# QUERY PARAM ROUTER
# ============================================================
_action = st.query_params.get("a")
if _action:
    st.query_params.clear()

    if _action == "new":
        st.session_state.messages = []
        st.session_state.current_artifact = None
        st.session_state.artifact_lang = None
        st.toast("Nova conversa iniciada", icon=":material/check_circle:")

    elif _action == "refresh":
        _cur = st.session_state.current_artifact
        st.session_state.current_artifact = None
        st.session_state.current_artifact = _cur
        st.toast("Preview atualizado", icon=":material/refresh:")

    elif _action == "example":
        st.session_state.pending_prompt = (
            "Crie uma landing page moderna para um produto SaaS de "
            "monitoramento de servidores. Use HTML, CSS e JavaScript "
            "em um unico arquivo. Paleta escura, tipografia sans-serif, "
            "secoes hero, features e footer."
        )

    elif _action == "mic":
        st.toast(
            "Gravacao de audio nao esta disponivel neste ambiente.",
            icon=":material/mic_off:",
        )

    elif _action in ("projects", "history", "settings"):
        st.toast("Modulo em desenvolvimento.", icon=":material/construction:")

    elif _action == "clear_attach":
        st.session_state.attached_name = None
        st.session_state.attached_text = None
        st.toast("Anexo removido", icon=":material/delete:")

    elif _action == "clear_chat":
        st.session_state.messages = []
        st.session_state.current_artifact = None
        st.rerun()


# ============================================================
# HELPERS
# ============================================================
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF"
    "\U0001F700-\U0001F77F\U0000FE00-\U0000FE0F\U00002B00-\U00002BFF"
    "\U00002190-\U000021FF"
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    if not text:
        return text
    cleaned = _EMOJI_RE.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +\n", "\n", cleaned)
    return cleaned


_THINK_RE    = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_ARTIFACT_RE = re.compile(r"<artifact[^>]*>(.*?)</artifact>", re.DOTALL | re.IGNORECASE)
_HTML_BLOCK  = re.compile(r"```html\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_SVG_BLOCK   = re.compile(r"```svg\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_DANGLING_RE = re.compile(r"<(thinking|artifact)\b[^>]*>(?![^<]*</\1>)", re.IGNORECASE)


def _strip_dangling(text: str) -> str:
    return _DANGLING_RE.sub("", text)


def extract_thinking(text: str):
    blocks = _THINK_RE.findall(text)
    thinking = "\n\n".join(b.strip() for b in blocks)
    return _THINK_RE.sub("", text).strip(), thinking.strip()


def _detect_lang(code: str) -> str:
    """Detecta a linguagem do artifact: 'svg' ou 'html'."""
    if not code:
        return "html"
    lowered = code.lower()
    has_svg = "<svg" in lowered
    has_html = "<html" in lowered or "<!doctype" in lowered
    return "svg" if (has_svg and not has_html) else "html"


def extract_artifact(text: str):
    m = _ARTIFACT_RE.search(text)
    if m:
        code = m.group(1).strip()
        return _ARTIFACT_RE.sub("", text).strip(), code, _detect_lang(code)

    m = _HTML_BLOCK.search(text)
    if m:
        code = m.group(1).strip()
        return _HTML_BLOCK.sub("", text).strip(), code, "html"

    m = _SVG_BLOCK.search(text)
    if m:
        svg = m.group(1).strip()
        wrapped = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>html,body{margin:0;padding:0;background:#fbfaf7;}"
            "body{display:flex;align-items:center;justify-content:center;"
            "min-height:100vh;}</style></head><body>"
            f"{svg}</body></html>"
        )
        return _SVG_BLOCK.sub("", text).strip(), wrapped, "svg"

    return text.strip(), None, None


def parse_response(raw: str) -> dict:
    no_artifact, artifact, lang = extract_artifact(raw)
    visible, thinking = extract_thinking(no_artifact)
    return {
        "text":     strip_emojis(visible),
        "thinking": thinking,
        "artifact": artifact,
        "lang":     lang,
    }


def _download_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"aether-artifact-{stamp}.html"


# ============================================================
# CONSTANTES DE LAYOUT
# ============================================================
PANEL_HEIGHT = 610          # altura fixa dos paineis (chat e preview)
IFRAME_HEIGHT = 560         # altura do iframe dentro do preview


# ============================================================
# CSS
# ============================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    :root, html, body {
        color-scheme: light !important;
    }
    :root {
        --background-color: #fafaf9 !important;
        --text-color: #1a1a1a !important;
        --secondary-background-color: #ffffff !important;
        --primary-color: #c96442 !important;
    }

    :root {
        --bg:           #fafaf9;
        --card:         #ffffff;
        --panel:        #f5f5f3;
        --bg-user:      #f0eee6;
        --bg-code:      #f5f5f3;
        --border:       #e8e8e5;
        --border-soft:  #f0f0ed;
        --text:         #1a1a1a;
        --text-dim:     #666666;
        --text-mute:    #999999;
        --accent:       #c96442;
        --accent-hover: #b85738;
        --shadow-sm:    0 1px 2px rgba(0,0,0,.03);
        --radius-sm:    8px;
        --radius-md:    10px;
        --radius-lg:    14px;
        --panel-h:      610px;
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
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
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
        padding: 0.5rem 1.25rem 0.4rem 1.25rem !important;
        max-width: 100% !important;
    }

    /* ---------- ALTURA FIXA DOS PAINEIS (610px) ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]),
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"]) {
        height: var(--panel-h) !important;
        max-height: var(--panel-h) !important;
        min-height: var(--panel-h) !important;
        overflow: hidden !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        height: 100% !important;
        overflow-y: auto !important;
    }

    /* ---------- SIDEBAR ---------- */
    section[data-testid="stSidebar"] {
        width: 220px !important;
        min-width: 220px !important;
        max-width: 220px !important;
        background-color: var(--card) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.85rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.15rem !important;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] button,
    button[kind="header"] { display: none !important; }

    .sb-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 2px 14px 2px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--border-soft);
    }
    .sb-brand-mark {
        width: 32px;
        height: 32px;
        background: var(--accent);
        color: #ffffff;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 17px;
        font-weight: 500;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(201,100,66,.22);
    }
    .sb-brand-info { display: flex; flex-direction: column; line-height: 1.15; }
    .sb-brand-name {
        font-size: 13.5px;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.01em;
    }
    .sb-brand-tag {
        font-size: 10.5px;
        color: var(--text-mute);
        letter-spacing: 0.02em;
    }

    .sb-section {
        font-size: 10px;
        font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.09em;
        text-transform: uppercase;
        padding: 14px 8px 6px 8px;
    }

    .sb-btn {
        display: flex !important;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        margin: 1px 0;
        border-radius: var(--radius-sm);
        color: var(--text-dim) !important;
        font-size: 13px;
        font-weight: 500;
        text-decoration: none !important;
        transition: background-color 0.15s ease, color 0.15s ease;
        cursor: pointer;
        line-height: 1.2;
    }
    .sb-btn:hover {
        background: var(--panel);
        color: var(--text) !important;
        text-decoration: none !important;
    }
    .sb-btn svg { flex-shrink: 0; opacity: 0.75; }
    .sb-btn:hover svg { opacity: 1; }
    .sb-btn span { color: inherit; }

    .sb-btn-primary {
        background: var(--accent);
        color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(201,100,66,.25);
        margin-bottom: 4px;
    }
    .sb-btn-primary:hover {
        background: var(--accent-hover);
        color: #ffffff !important;
    }
    .sb-btn-primary svg { opacity: 1; }

    .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
        color: var(--text);
    }

    input, textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--accent) !important;
        background-color: transparent !important;
    }
    input::placeholder, textarea::placeholder {
        color: var(--text-mute) !important;
        -webkit-text-fill-color: var(--text-mute) !important;
        opacity: 1 !important;
    }

    /* ---------- APP HEADER ---------- */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 20px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        margin-bottom: 10px;
        box-shadow: var(--shadow-sm);
    }
    .app-header-left { display: flex; align-items: center; gap: 12px; }
    .app-brand-mark {
        width: 34px;
        height: 34px;
        background: var(--accent);
        color: #ffffff;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 18px;
        font-weight: 500;
        box-shadow: 0 2px 6px rgba(201,100,66,.22);
        flex-shrink: 0;
    }
    .app-brand-info { line-height: 1.15; }
    .app-brand-name {
        font-size: 15px;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.015em;
    }
    .app-brand-tag {
        font-size: 11.5px;
        color: var(--text-mute);
        margin-top: 1px;
    }
    .app-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 12px;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        font-size: 12px;
        font-weight: 500;
        color: var(--text-dim);
    }
    .app-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #6ba944;
        box-shadow: 0 0 0 3px rgba(107,169,68,.15);
    }

    /* ---------- PANEL LABELS ---------- */
    .panel-label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 2px 4px 8px 4px;
        font-size: 11px;
        font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .panel-label-title { display: flex; align-items: center; gap: 8px; }
    .panel-label-tools { display: flex; gap: 3px; align-items: center; }
    .panel-tool {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-mute) !important;
        border-radius: 6px;
        text-decoration: none !important;
        cursor: pointer;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .panel-tool:hover {
        background: var(--panel);
        color: var(--accent) !important;
        text-decoration: none !important;
    }

    /* ---------- DOWNLOAD BUTTON (preview header) ---------- */
    [data-testid="stDownloadButton"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stDownloadButton"] > button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        height: 28px !important;
        min-height: 28px !important;
        padding: 0 10px 0 8px !important;
        width: 100% !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        cursor: pointer !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    [data-testid="stDownloadButton"] > button:focus {
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stDownloadButton"] > button p {
        color: inherit !important;
        font-size: 12px !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }

    /* ---------- CHAT ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"]) {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm);
        padding: 4px 18px !important;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 6px 0 !important;
        margin-bottom: 8px !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: flex-start !important;
        gap: 0 !important;
        animation: fadeUp 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    [data-testid="stChatMessage"] img {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    [data-testid="stChatMessageContent"] {
        flex: 1 1 auto !important;
        max-width: 100% !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
    }

    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) {
        flex-direction: row-reverse !important;
        margin: 6px 0 12px 0 !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-user) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-lg) !important;
        padding: 12px 18px !important;
        max-width: 82% !important;
        flex: 0 1 auto !important;
    }

    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) {
        margin-bottom: 16px !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"]::before {
        content: "AETHER";
        display: block;
        font-size: 10.5px;
        font-weight: 700;
        color: var(--text-mute);
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li {
        color: var(--text) !important;
        font-size: 14.5px;
        line-height: 1.65;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(3px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatMessage"] [data-testid="stCode"],
    [data-testid="stChatMessage"] pre {
        background: var(--bg-code) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stChatMessage"] pre code,
    [data-testid="stChatMessage"] [data-testid="stCode"] code {
        background: transparent !important;
        color: var(--text) !important;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace !important;
        font-size: 12.5px !important;
        line-height: 1.6 !important;
    }
    [data-testid="stChatMessage"] p code,
    [data-testid="stChatMessage"] li code {
        background: var(--bg-code) !important;
        color: var(--text) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid var(--border-soft) !important;
        font-size: 12.5px !important;
    }

    [data-testid="stChatMessage"] [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        margin: 0 0 8px 0 !important;
        padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary {
        padding: 2px 0 !important;
        font-size: 12px !important;
        color: var(--text-mute) !important;
        font-weight: 500 !important;
        background: transparent !important;
        border: none !important;
        list-style: none !important;
        opacity: 0.8;
        transition: opacity 0.15s ease, color 0.15s ease;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary:hover {
        opacity: 1;
        color: var(--accent) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary p {
        font-size: 12px !important;
        color: inherit !important;
        display: inline !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary svg {
        width: 10px !important;
        height: 10px !important;
        opacity: 0.6;
        margin-right: 6px;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {
        border-left: 2px solid var(--border-soft) !important;
        padding: 6px 0 6px 14px !important;
        margin: 6px 0 10px 0 !important;
        background: transparent !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] p {
        font-size: 12.5px !important;
        color: var(--text-dim) !important;
        line-height: 1.65;
        font-style: italic;
        opacity: 0.9;
    }

    /* ---------- COMPOSER ---------- */
    [data-testid="stForm"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 6px 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
        margin-top: 4px;
    }
    [data-testid="stForm"] > div > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 6px !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] > div {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input {
        background: transparent !important;
        border: none !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--accent) !important;
        font-size: 14.5px !important;
        padding: 12px 6px !important;
        height: 44px !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
        color: var(--text-mute) !important;
        -webkit-text-fill-color: var(--text-mute) !important;
        opacity: 1 !important;
    }

    [data-testid="stForm"] [data-testid="stPopover"] > button {
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        padding: 0 !important;
        font-size: 0 !important;
        color: transparent !important;
        background-color: transparent !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23999999' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        transition: border-color 0.15s ease, background-color 0.15s ease !important;
    }
    [data-testid="stForm"] [data-testid="stPopover"] > button:hover {
        background-color: var(--panel) !important;
        border-color: var(--accent) !important;
    }

    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        padding: 0 !important;
        font-size: 0 !important;
        box-shadow: 0 2px 6px rgba(201,100,66,.28) !important;
        transition: background-color 0.15s ease, transform 0.15s ease !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 2L11 13M22 2l-7 20-4-9-9-4z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        background-color: var(--accent-hover) !important;
        transform: translateY(-1px);
    }

    .composer-mic {
        width: 40px !important;
        height: 40px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: var(--text-mute) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        text-decoration: none !important;
        background: transparent;
        transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
    }
    .composer-mic:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--panel);
        text-decoration: none !important;
    }

    .attach-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-sm);
        font-size: 12px;
        color: var(--text-dim) !important;
        margin: 4px 0 6px 0;
    }
    .attach-chip span { color: var(--text-dim) !important; }
    .attach-chip a {
        color: var(--text-mute) !important;
        text-decoration: none;
        font-weight: 600;
        margin-left: 4px;
        transition: color 0.15s ease;
    }
    .attach-chip a:hover { color: var(--accent) !important; }

    /* ---------- PREVIEW ---------- */
    .preview-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 40px 24px;
        min-height: 480px;
    }
    .preview-empty-icon {
        width: 78px;
        height: 78px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: 50%;
        color: var(--text-mute);
        margin-bottom: 22px;
    }
    .preview-empty-title {
        font-size: 15.5px;
        font-weight: 600;
        color: var(--text) !important;
        margin-bottom: 8px;
        letter-spacing: -0.01em;
    }
    .preview-empty-text {
        font-size: 13px;
        color: var(--text-mute) !important;
        line-height: 1.6;
        max-width: 320px;
        margin-bottom: 20px;
    }
    .preview-empty-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: var(--card);
        color: var(--text) !important;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none !important;
        transition: border-color 0.15s ease, color 0.15s ease;
    }
    .preview-empty-btn:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
        text-decoration: none !important;
    }

    iframe {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        background: #ffffff !important;
    }

    .cursor {
        display: inline-block;
        width: 2px;
        height: 1.05em;
        background: var(--accent);
        vertical-align: text-bottom;
        margin-left: 2px;
        animation: blink 1s step-start infinite;
        opacity: 0.7;
    }
    @keyframes blink { 50% { opacity: 0; } }

    /* ---------- GENERIC BUTTONS ---------- */
    .stButton > button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.5rem 1rem !important;
        transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease !important;
        box-shadow: none !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    .stButton > button:focus { box-shadow: none !important; outline: none !important; }
    .stButton > button p { color: inherit !important; margin: 0 !important; }

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
        box-shadow: 0 4px 20px rgba(0,0,0,.08) !important;
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
    }
    .stAlert * { color: var(--text) !important; }

    [data-testid="stToast"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,.08) !important;
    }
    [data-testid="stToast"] * { color: var(--text) !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: #dedbd3;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #c9c6be; }

    /* ---------- MENU MOBILE ---------- */
    /* Esconde o botao de menu nativo no desktop (ja temos a sidebar fixa). */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Em telas pequenas: libera o toggle nativo + overlay da sidebar. */
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
            top: 12px !important;
            left: 12px !important;
        }

        section[data-testid="stSidebar"] {
            width: 240px !important;
            min-width: 240px !important;
            max-width: 240px !important;
            box-shadow: 2px 0 18px rgba(0,0,0,.08);
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            margin-left: -240px !important;
            transition: margin-left 0.2s ease;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            transition: margin-left 0.2s ease;
        }

        .app-header {
            padding: 10px 14px 10px 56px !important;
            margin-bottom: 8px;
        }
        .app-brand-tag { display: none; }

        [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"]) {
            height: var(--panel-h) !important;
            max-height: var(--panel-h) !important;
            min-height: var(--panel-h) !important;
        }

        .preview-empty { min-height: 420px; padding: 30px 20px; }
    }

    @media (max-width: 640px) {
        .block-container {
            padding: 0.4rem 0.75rem 0.4rem 0.75rem !important;
        }
        .app-header {
            padding: 8px 12px 8px 52px !important;
        }
        .app-brand-name { font-size: 14px; }
        .app-status { padding: 5px 10px; font-size: 11px; }
        .preview-empty { min-height: 340px; padding: 24px 16px; }
        .preview-empty-icon { width: 64px; height: 64px; margin-bottom: 16px; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
    <div class="sb-brand">
        <div class="sb-brand-mark">A</div>
        <div class="sb-brand-info">
            <div class="sb-brand-name">Aether</div>
            <div class="sb-brand-tag">Workspace</div>
        </div>
    </div>

    <a class="sb-btn sb-btn-primary" href="?a=new" target="_self">
        {ICON_PLUS}<span>Novo projeto</span>
    </a>

    <div class="sb-section">Espaco</div>
    <a class="sb-btn" href="?a=projects" target="_self">
        {ICON_FOLDER}<span>Projetos</span>
    </a>
    <a class="sb-btn" href="?a=history" target="_self">
        {ICON_HISTORY}<span>Historico</span>
    </a>

    <div class="sb-section">Sistema</div>
    <a class="sb-btn" href="?a=settings" target="_self">
        {ICON_GEAR}<span>Configuracoes</span>
    </a>
    <a class="sb-btn" href="?a=clear_chat" target="_self">
        {ICON_TRASH}<span>Limpar conversa</span>
    </a>
    """, unsafe_allow_html=True)


# ============================================================
# APP HEADER
# ============================================================
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <div class="app-brand-mark">A</div>
        <div class="app-brand-info">
            <div class="app-brand-name">Aether Engine</div>
            <div class="app-brand-tag">Espaco de trabalho conversacional</div>
        </div>
    </div>
    <div class="app-status">
        <span class="app-status-dot"></span>
        <span>Online</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LAYOUT
# ============================================================
col_chat, col_preview = st.columns([1, 1.15], gap="medium")


# ------------------------------------------------------------
# CHAT
# ------------------------------------------------------------
_do_rerun = False

with col_chat:

    st.markdown(
        '<div class="panel-label"><span class="panel-label-title">Conversa</span></div>',
        unsafe_allow_html=True,
    )

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

    chat_box = st.container(height=PANEL_HEIGHT)

    with chat_box:
        if not st.session_state.messages:
            st.markdown(
                '<div style="padding: 40px 20px; text-align: center; '
                'color: #999; font-size: 13px;">'
                'Envie uma mensagem para comecar uma nova conversa.'
                '</div>',
                unsafe_allow_html=True,
            )

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user", avatar=_AVATAR_USER):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar=_AVATAR_AI):
                    if msg.get("thinking"):
                        with st.expander("Processando raciocinio"):
                            st.markdown(msg["thinking"])
                    if msg.get("content"):
                        st.markdown(msg["content"])

        if _prompt:
            with st.chat_message("assistant", avatar=_AVATAR_AI):

                thinking_slot = st.expander("Processando raciocinio", expanded=False)
                with thinking_slot:
                    thinking_body = st.empty()

                text_body = st.empty()

                raw_buffer = ""
                reasoning_accum = ""

                try:
                    api_messages = (
                        [{"role": "system", "content": SYSTEM_PROMPT}]
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

                            partial_visible, partial_think = extract_thinking(raw_buffer)
                            partial_visible, _, _ = extract_artifact(partial_visible)
                            partial_visible = _strip_dangling(partial_visible)
                            partial_visible = strip_emojis(partial_visible)

                            combined = "\n\n".join(
                                filter(None, [reasoning_accum, partial_think])
                            )
                            if combined:
                                thinking_body.markdown(
                                    combined + '<span class="cursor"></span>',
                                    unsafe_allow_html=True,
                                )
                            if partial_visible:
                                text_body.markdown(
                                    partial_visible + '<span class="cursor"></span>',
                                    unsafe_allow_html=True,
                                )

                    parsed = parse_response(raw_buffer)
                    final_thinking = "\n\n".join(
                        filter(None, [reasoning_accum, parsed["thinking"]])
                    )

                    if final_thinking:
                        thinking_body.markdown(final_thinking)
                    else:
                        thinking_body.markdown("_Sem raciocinio exposto._")

                    text_body.markdown(parsed["text"] or "_Sem resposta._")

                    if parsed["artifact"]:
                        st.session_state.current_artifact = parsed["artifact"]
                        st.session_state.artifact_lang = parsed["lang"]

                    st.session_state.messages.append({
                        "role":     "assistant",
                        "content":  parsed["text"],
                        "thinking": final_thinking,
                    })

                except Exception as e:
                    st.error(f"Falha ao processar resposta: {e}")
                    st.session_state.messages.append({
                        "role":     "assistant",
                        "content":  f"Erro: {e}",
                        "thinking": "",
                    })

            st.session_state.attached_name = None
            st.session_state.attached_text = None
            _do_rerun = True

    if st.session_state.attached_name:
        st.markdown(
            f'<div class="attach-chip">'
            f'<span>{st.session_state.attached_name}</span>'
            f'<a href="?a=clear_attach" target="_self" title="Remover">remover</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

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
                placeholder="Envie uma mensagem para o Aether Engine...",
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


# ------------------------------------------------------------
# PREVIEW
# ------------------------------------------------------------
with col_preview:

    # Header do preview: titulo | refresh | download
    hdr_l, hdr_m, hdr_r = st.columns(
        [4.5, 0.55, 1.6],
        gap="small",
        vertical_alignment="center",
    )

    with hdr_l:
        st.markdown(
            '<div class="panel-label" style="padding:0;margin:0;">'
            '<span class="panel-label-title">Preview</span></div>',
            unsafe_allow_html=True,
        )

    with hdr_m:
        st.markdown(
            f'<a class="panel-tool" href="?a=refresh" target="_self" '
            f'title="Atualizar">{ICON_REFRESH}</a>',
            unsafe_allow_html=True,
        )

    with hdr_r:
        if st.session_state.current_artifact:
            st.download_button(
                label="Baixar HTML",
                data=st.session_state.current_artifact,
                file_name=_download_filename(),
                mime="text/html",
                use_container_width=True,
                key="dl_artifact",
            )

    preview_box = st.container(height=PANEL_HEIGHT)

    with preview_box:
        if st.session_state.current_artifact:
            components.html(
                st.session_state.current_artifact,
                height=IFRAME_HEIGHT,
                scrolling=True,
            )
        else:
            st.markdown(f"""
            <div class="preview-empty">
                <div class="preview-empty-icon">{ICON_IMAGE}</div>
                <div class="preview-empty-title">Seu preview aparecera aqui</div>
                <div class="preview-empty-text">
                    Peca ao Aether para gerar uma interface ou componente visual.
                </div>
                <a class="preview-empty-btn" href="?a=example" target="_self">
                    Ver exemplo
                </a>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# RERUN
# ============================================================
if _do_rerun:
    st.rerun()
