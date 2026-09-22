"""
Aether Engine — workspace conversacional
-----------------------------------------
Tema light forcado (imune ao dark mode do navegador).
Botoes funcionais via query params. Preview via current_artifact.
"""

import os
import re
import urllib.parse
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
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{path}</svg>'
    )

ICON_SPARK   = _svg('<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.9 2.6L22.5 18.5l-2.6.9L19 22l-.9-2.6L15.5 18.5l2.6-.9z"/>', 16)
ICON_PLUS    = _svg('<path d="M12 5v14M5 12h14"/>', 18)
ICON_FOLDER  = _svg('<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>', 18)
ICON_GEAR    = _svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>', 18)
ICON_USER    = _svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>', 18)
ICON_CLIP    = _svg('<path d="M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/>', 18)
ICON_MIC     = _svg('<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/>', 18)
ICON_REFRESH = _svg('<path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/>', 15)
ICON_FULL    = _svg('<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>', 15)
ICON_IMAGE   = _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>', 48)


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
    initial_sidebar_state="collapsed",
)


# ============================================================
# SESSION STATE
# ============================================================
_DEFAULTS = {
    "messages":         [],
    "current_artifact": None,       # <-- renomeado
    "artifact_lang":    None,
    "pending_prompt":   None,
    "fullscreen":       False,
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
        st.toast("Nova conversa iniciada", icon="✓")

    elif _action == "refresh":
        # Reatribui para forcar re-render do iframe
        _cur = st.session_state.current_artifact
        st.session_state.current_artifact = None
        st.session_state.current_artifact = _cur
        st.toast("Preview atualizado", icon="✓")

    elif _action == "fullscreen":
        st.session_state.fullscreen = not st.session_state.fullscreen

    elif _action == "example":
        st.session_state.pending_prompt = (
            "Crie uma landing page moderna para um produto SaaS de "
            "monitoramento de servidores. Use HTML, CSS e JavaScript "
            "em um unico arquivo. Paleta escura, tipografia sans-serif, "
            "secoes hero, features e footer."
        )

    elif _action == "mic":
        st.toast("Gravacao de audio nao esta disponivel neste ambiente.", icon="!")

    elif _action == "clear_attach":
        st.session_state.attached_name = None
        st.session_state.attached_text = None
        st.toast("Anexo removido", icon="✓")


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
    return "svg" if ("<svg" in code.lower() and "<html" not in code.lower()) else "html"


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


# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: light !important;
    }

    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"], .stDeployButton,
    [data-testid="stAppDeployButton"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; }

    :root {
        --bg:           #fbfaf7;
        --bg-2:         #f5f3ee;
        --bg-user:      #f0eee6;
        --bg-code:      #f5f3ee;
        --border:       #e5e2da;
        --border-soft:  #efece4;
        --text:         #1a1a1a;
        --text-dim:     #5c5851;
        --text-mute:    #9a9388;
        --accent:       #c96442;
        --accent-dark:  #b85738;
        --shadow-sm:    0 1px 2px rgba(0,0,0,.03);
        --radius-sm:    8px;
        --radius-md:    12px;
        --radius-pill:  999px;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: var(--text) !important;
        -webkit-font-smoothing: antialiased;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
    }

    .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
        color: var(--text);
    }

    input, textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stChatInput"] textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: var(--text) !important;
        background-color: transparent !important;
        caret-color: var(--accent) !important;
    }
    input::placeholder, textarea::placeholder {
        color: var(--text-mute) !important;
        opacity: 1 !important;
    }
    [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"] {
        background-color: transparent !important;
        border-color: var(--border) !important;
    }

    .block-container {
        padding: 0.6rem 1rem 0.6rem 1rem !important;
        max-width: 100% !important;
    }

    /* ---------- TOPBAR ---------- */
    .topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 18px;
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        margin-bottom: 12px;
    }
    .topbar-left { display: flex; align-items: center; gap: 14px; }
    .topbar-brand { display: flex; align-items: center; gap: 10px; }
    .brand-mark {
        width: 28px; height: 28px;
        background: var(--accent); color: #fff !important;
        border-radius: var(--radius-sm);
        display: flex; align-items: center; justify-content: center;
        font-family: Georgia, serif; font-size: 15px; font-weight: 500;
        box-shadow: 0 2px 6px rgba(201,100,66,.25);
    }
    .brand-name { font-size: 15px; font-weight: 600; color: var(--text) !important; }
    .brand-tag  { font-size: 11px; color: var(--text-mute) !important; margin-top: -2px; }
    .topbar-right { display: flex; align-items: center; gap: 6px; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 5px 11px;
        background: var(--bg-2);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-pill);
        font-size: 11px; color: var(--text-dim) !important;
    }
    .status-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #6ba944;
        box-shadow: 0 0 0 3px rgba(107, 169, 68, 0.15);
    }

    /* ---------- PANEL LABEL ---------- */
    .panel-label {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 4px 10px 4px;
        font-size: 11px; font-weight: 600;
        color: var(--text-mute) !important;
        letter-spacing: 0.08em; text-transform: uppercase;
    }
    .panel-label span { color: var(--text-mute) !important; }
    .panel-label-tools { display: flex; gap: 2px; }
    .panel-tool {
        width: 26px; height: 26px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-mute) !important;
        border-radius: 6px;
        text-decoration: none !important;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .panel-tool:hover {
        background: var(--bg-2);
        color: var(--text) !important;
    }

    /* ---------- RAIL ---------- */
    .rail {
        display: flex; flex-direction: column; align-items: center;
        gap: 4px; padding: 12px 0;
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
    }
    .rail-btn {
        width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-dim) !important;
        border-radius: var(--radius-sm);
        cursor: pointer;
        text-decoration: none !important;
        transition: all 0.2s ease;
    }
    .rail-btn:hover {
        background: var(--bg-2);
        color: var(--accent) !important;
        transform: translateY(-1px);
    }
    .rail-btn.primary {
        background: var(--accent);
        color: #fff !important;
        box-shadow: 0 2px 6px rgba(201,100,66,.25);
    }
    .rail-btn.primary:hover {
        background: var(--accent-dark);
        color: #fff !important;
    }
    .rail-divider {
        width: 20px; height: 1px;
        background: var(--border-soft);
        margin: 6px 0;
    }
    .rail-spacer { flex: 1; }

    /* ---------- CONTAINERS ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"]) {
        background: #ffffff;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm);
        padding: 6px 14px !important;
    }

    /* ---------- MESSAGES ---------- */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 8px 0 !important;
        margin-bottom: 4px !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: flex-start !important;
        gap: 0 !important;
        animation: fadeUp 0.32s cubic-bezier(0.16, 1, 0.3, 1);
    }
    [data-testid="stChatMessage"] img {
        display: none !important;
        width: 0 !important; height: 0 !important;
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
        margin: 4px 0 14px 0 !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-user) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-md) !important;
        padding: 11px 16px !important;
        max-width: 82% !important;
        flex: 0 1 auto !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) {
        margin-bottom: 20px !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"]::before {
        content: "Aether Engine";
        display: block;
        font-size: 11px; font-weight: 600;
        color: var(--text-mute) !important;
        letter-spacing: 0.04em; text-transform: uppercase;
        margin-bottom: 8px;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li {
        color: var(--text) !important;
        font-size: 15px; line-height: 1.65;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ---------- CODE ---------- */
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
        font-size: 13px !important;
    }
    [data-testid="stChatMessage"] p code,
    [data-testid="stChatMessage"] li code {
        background: var(--bg-code) !important;
        color: var(--text) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid var(--border-soft) !important;
        font-size: 13px !important;
    }

    /* ---------- THINKING ---------- */
    [data-testid="stChatMessage"] [data-testid="stExpander"] {
        border: none !important; background: transparent !important;
        margin: 0 0 8px 0 !important; padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] details {
        border: none !important; background: transparent !important; padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary {
        padding: 2px 0 !important;
        font-size: 12px !important;
        color: var(--text-mute) !important;
        font-weight: 400 !important;
        background: transparent !important;
        border: none !important;
        list-style: none !important;
        opacity: 0.75;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary:hover {
        opacity: 1; color: var(--text-dim) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary p {
        font-size: 12px !important; color: inherit !important; display: inline !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary svg {
        width: 10px !important; height: 10px !important;
        opacity: 0.6; margin-right: 6px;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {
        border-left: 1px solid var(--border) !important;
        padding: 6px 0 6px 14px !important;
        margin: 6px 0 10px 0 !important;
        background: transparent !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] p {
        font-size: 13px !important;
        color: var(--text-dim) !important;
        line-height: 1.65; font-style: italic;
    }

    /* ---------- COMPOSER ---------- */
    [data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 8px 10px !important;
        box-shadow: var(--shadow-sm);
        margin-top: 8px;
    }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 4px !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] > div {
        border: none !important; background: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input {
        background: transparent !important;
        border: none !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--accent) !important;
        font-size: 15px !important;
        padding: 10px 6px !important;
        height: 42px !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
        color: var(--text-mute) !important;
        -webkit-text-fill-color: var(--text-mute) !important;
        opacity: 1 !important;
    }
    [data-testid="stForm"] [data-testid="stPopover"] > button {
        width: 38px !important; height: 38px !important;
        min-width: 38px !important;
        color: var(--text-mute) !important;
        font-size: 0 !important;
    }
    [data-testid="stForm"] [data-testid="stPopover"] > button:hover {
        background: var(--bg-2) !important;
        color: var(--accent) !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        width: 42px !important; height: 42px !important;
        min-width: 42px !important;
        padding: 0 !important;
        font-size: 0 !important;
        box-shadow: 0 2px 6px rgba(201,100,66,.28) !important;
        position: relative;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button::after {
        content: "";
        position: absolute; inset: 0;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 2L11 13M22 2l-7 20-4-9-9-4z'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        pointer-events: none;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        background: var(--accent-dark) !important;
        transform: translateY(-1px);
    }

    iframe {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        background: #ffffff !important;
    }

    /* ---------- CURSOR ---------- */
    .cursor {
        display: inline-block;
        width: 2px; height: 1.05em;
        background: var(--text);
        vertical-align: text-bottom;
        margin-left: 2px;
        animation: blink 1s step-start infinite;
        opacity: 0.65;
    }
    @keyframes blink { 50% { opacity: 0; } }

    /* ---------- ATTACH CHIP ---------- */
    .attach-chip {
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 10px;
        background: var(--bg-2);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-sm);
        font-size: 12px; color: var(--text-dim) !important;
        margin: 4px 0 8px 0;
    }
    .attach-chip span { color: var(--text-dim) !important; }
    .attach-chip a {
        color: var(--text-mute) !important;
        text-decoration: none;
        margin-left: 4px;
    }
    .attach-chip a:hover { color: var(--accent) !important; }

    /* ---------- MISC ---------- */
    .stButton > button {
        background: #ffffff !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.45rem 1rem !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    .stButton > button p { color: inherit !important; }

    [data-testid="stFileUploader"] section {
        background: var(--bg-2) !important;
        border: 1px dashed var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stFileUploader"] section * { color: var(--text) !important; }

    .stAlert {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-2) !important;
        color: var(--text) !important;
    }
    .stAlert * { color: var(--text) !important; }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #dedbd3; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #c9c6be; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# TOPBAR
# ============================================================
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-brand">
      <div class="brand-mark">A</div>
      <div>
        <div class="brand-name">Aether Engine</div>
        <div class="brand-tag">Espaco de trabalho conversacional</div>
      </div>
    </div>
  </div>
  <div class="topbar-right">
    <div class="status-pill"><span class="status-dot"></span> Online</div>
  </div>
</div>
""", unsafe_allow_html=True)

tb1, tb2, tb3, tb4 = st.columns([10, 0.6, 0.6, 0.6], gap="small")
with tb3:
    with st.popover("folder", use_container_width=False):
        st.markdown("**Projetos**")
        st.markdown("- Default workspace")
        st.markdown("- Landing pages")
        st.markdown("- Dashboards")
        if st.button("Novo projeto", use_container_width=True):
            st.toast("Funcionalidade em desenvolvimento", icon="!")
with tb4:
    with st.popover("user", use_container_width=False):
        st.markdown("**Perfil**")
        st.markdown("Sessao local")
        st.caption(f"Mensagens nesta sessao: {len(st.session_state.messages)}")
        if st.button("Limpar historico", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_artifact = None
            st.rerun()


# ============================================================
# LAYOUT
# ============================================================
if st.session_state.fullscreen:
    rail_col, preview_col = st.columns([0.35, 8], gap="small")
    chat_col = None
else:
    rail_col, chat_col, preview_col = st.columns([0.35, 1.15, 1], gap="small")


# ------------------------------------------------------------
# RAIL
# ------------------------------------------------------------
with rail_col:
    st.markdown(f"""
    <div class="rail">
      <a class="rail-btn primary" href="?a=new" title="Nova conversa" target="_self">{ICON_PLUS}</a>
      <div class="rail-divider"></div>
      <a class="rail-btn" href="?a=example" title="Exemplo" target="_self">{ICON_SPARK}</a>
      <div class="rail-btn" title="Projetos">{ICON_FOLDER}</div>
      <div class="rail-spacer"></div>
      <div class="rail-divider"></div>
      <div class="rail-btn" title="Configuracoes">{ICON_GEAR}</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# CHAT
# ------------------------------------------------------------
_pending_from_render = None

if chat_col is not None:
    with chat_col:

        st.markdown(
            '<div class="panel-label"><span>Conversa</span></div>',
            unsafe_allow_html=True,
        )

        chat_box = st.container(height=520)

        with chat_box:
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

        if st.session_state.attached_name:
            st.markdown(
                f'<div class="attach-chip">'
                f'<span>{st.session_state.attached_name}</span>'
                f'<a href="?a=clear_attach" target="_self" title="Remover">x</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.form("composer", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(
                [0.4, 6, 0.4, 0.85],
                gap="small",
                vertical_alignment="center",
            )
            with c1:
                with st.popover("clip", use_container_width=False):
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
                    f'<a class="panel-tool" href="?a=mic" target="_self" '
                    f'title="Gravar audio" style="width:38px;height:38px;">'
                    f'{ICON_MIC}</a>',
                    unsafe_allow_html=True,
                )
            with c4:
                submitted = st.form_submit_button("Enviar")

        if submitted and user_msg.strip():
            _pending_from_render = user_msg.strip()


# ------------------------------------------------------------
# PREVIEW  —  BLOCO SUBSTITUIDO
# ------------------------------------------------------------
with preview_col:

    fs_icon = "✕" if st.session_state.fullscreen else ICON_FULL
    st.markdown(f"""
    <div class="panel-label">
      <span>Preview</span>
      <div class="panel-label-tools">
        <a class="panel-tool" href="?a=refresh" target="_self" title="Atualizar">{ICON_REFRESH}</a>
        <a class="panel-tool" href="?a=fullscreen" target="_self" title="Tela cheia">{fs_icon}</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Bloco substituido (exatamente como pedido) ----
    if st.session_state.current_artifact:
        components.html(
            st.session_state.current_artifact,
            height=750,
            scrolling=True,
        )
    else:
        st.markdown(
            '<div style="border: 1px dashed #222; border-radius: 8px; height: 750px; '
            'display: flex; align-items: center; justify-content: center; color: #444; font-size: 14px;">'
            'Nenhum componente visual foi gerado ainda.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Codigo-fonte colapsado abaixo (opcional, nao quebra o preview)
    if st.session_state.current_artifact:
        with st.expander("Ver codigo-fonte"):
            st.code(
                st.session_state.current_artifact,
                language=st.session_state.artifact_lang or "html",
            )


# ============================================================
# PROCESSAR PROMPT PENDENTE
# ============================================================
_prompt = st.session_state.pending_prompt or _pending_from_render
if _prompt:
    st.session_state.pending_prompt = None

    if st.session_state.attached_text:
        _prompt = (
            f"{_prompt}\n\n"
            f"[Arquivo anexado: {st.session_state.attached_name}]\n"
            f"```\n{st.session_state.attached_text[:4000]}\n```"
        )

    st.session_state.messages.append({"role": "user", "content": _prompt})

    if chat_col is not None:
        with chat_col:
            with st.chat_message("user", avatar=_AVATAR_USER):
                st.markdown(_prompt)

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

    st.rerun()
