"""
Aether Engine — workspace conversacional
-----------------------------------------
Layout de 3 colunas (rail + chat + preview), input expandido com
icones de anexo/microfone, preview com toolbar, feedback animado.
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
# AVATARES INVISIVEIS (apenas para targeting CSS)
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
# ICONES SVG (Lucide-style)
# ============================================================
def _svg(path: str, size: int = 18) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{path}</svg>'
    )

ICON_SPARK = _svg(
    '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>'
    '<path d="M19 15l.9 2.6L22.5 18.5l-2.6.9L19 22l-.9-2.6L15.5 18.5l2.6-.9z"/>',
    16,
)
ICON_PLUS    = _svg('<path d="M12 5v14M5 12h14"/>', 18)
ICON_FOLDER  = _svg(
    '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    18,
)
ICON_GEAR    = _svg(
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    18,
)
ICON_USER    = _svg(
    '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    18,
)
ICON_CLIP    = _svg(
    '<path d="M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/>',
    18,
)
ICON_MIC     = _svg(
    '<rect x="9" y="2" width="6" height="12" rx="3"/>'
    '<path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/>',
    18,
)
ICON_SEND    = _svg(
    '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
    18,
)
ICON_REFRESH = _svg(
    '<path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5"/>'
    '<path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5"/>',
    15,
)
ICON_FULL    = _svg(
    '<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>',
    15,
)
ICON_ZOOM_IN  = _svg('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M11 8v6M8 11h6"/>', 15)
ICON_ZOOM_OUT = _svg('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M8 11h6"/>', 15)
ICON_COPY    = _svg(
    '<rect x="9" y="9" width="12" height="12" rx="2"/>'
    '<path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    15,
)
ICON_IMAGE   = _svg(
    '<rect x="3" y="3" width="18" height="18" rx="2"/>'
    '<circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>',
    48,
)


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
# CSS
# ============================================================
st.markdown("""
<style>
    /* ---------- HIDE STREAMLIT ---------- */
    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    [data-testid="stDeployButton"], .stDeployButton,
    [data-testid="stAppDeployButton"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; }

    /* ---------- TOKENS ---------- */
    :root {
        --bg:           #fbfaf7;
        --bg-2:         #f5f3ee;
        --bg-3:         #efece4;
        --bg-user:      #f0eee6;
        --bg-code:      #f5f3ee;
        --border:       #e5e2da;
        --border-soft:  #efece4;
        --text:         #1a1a1a;
        --text-dim:     #5c5851;
        --text-mute:    #9a9388;
        --accent:       #c96442;
        --accent-soft:  rgba(201, 100, 66, 0.08);
        --shadow-sm:    0 1px 2px rgba(0,0,0,.03);
        --shadow-md:    0 4px 14px rgba(0,0,0,.06);
        --radius-sm:    8px;
        --radius-md:    12px;
        --radius-pill:  999px;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: var(--text);
        -webkit-font-smoothing: antialiased;
    }

    /* ---------- APP SHELL ---------- */
    .stApp { background: var(--bg); }
    .block-container {
        padding: 0.6rem 1rem 0.6rem 1rem !important;
        max-width: 100% !important;
    }

    /* ---------- TOP BAR ---------- */
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
    .topbar-brand {
        display: flex; align-items: center; gap: 10px;
    }
    .brand-mark {
        width: 28px; height: 28px;
        background: var(--accent);
        color: #fff;
        border-radius: var(--radius-sm);
        display: flex; align-items: center; justify-content: center;
        font-family: Georgia, serif;
        font-size: 15px; font-weight: 500;
        box-shadow: 0 2px 6px rgba(201,100,66,.25);
    }
    .brand-name {
        font-size: 15px; font-weight: 600;
        color: var(--text); letter-spacing: -0.01em;
    }
    .brand-tag {
        font-size: 11px; color: var(--text-mute);
        letter-spacing: 0.01em; margin-top: -2px;
    }
    .topbar-right { display: flex; align-items: center; gap: 6px; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 5px 11px;
        background: var(--bg-2);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-pill);
        font-size: 11px; color: var(--text-dim);
        font-weight: 500; letter-spacing: 0.02em;
    }
    .status-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #6ba944;
        box-shadow: 0 0 0 3px rgba(107, 169, 68, 0.15);
    }
    .topbar-menu {
        display: flex; gap: 2px; margin-left: 8px;
    }
    .menu-btn {
        width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-dim);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .menu-btn:hover {
        background: var(--bg-2);
        color: var(--accent);
    }

    /* ---------- PANEL LABEL ---------- */
    .panel-label {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 4px 10px 4px;
        font-size: 11px; font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.08em; text-transform: uppercase;
    }
    .panel-label-tools {
        display: flex; gap: 2px;
    }
    .panel-tool {
        width: 26px; height: 26px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-mute);
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .panel-tool:hover {
        background: var(--bg-2);
        color: var(--text);
    }

    /* ---------- RAIL ---------- */
    .rail {
        display: flex; flex-direction: column; align-items: center;
        gap: 4px;
        padding: 12px 0;
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
    }
    .rail-btn {
        width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-dim);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .rail-btn:hover {
        background: var(--bg-2);
        color: var(--accent);
        transform: translateY(-1px);
    }
    .rail-btn.primary {
        background: var(--accent);
        color: #fff;
        box-shadow: 0 2px 6px rgba(201,100,66,.25);
    }
    .rail-btn.primary:hover {
        background: #b85738;
        color: #fff;
    }
    .rail-divider {
        width: 20px; height: 1px;
        background: var(--border-soft);
        margin: 6px 0;
    }
    .rail-spacer { flex: 1; }

    /* ---------- CONTAINERS WITH HEIGHT ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"]) {
        background: #ffffff;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm);
        padding: 6px 14px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
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

    /* User bubble */
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

    /* Assistant */
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) {
        margin-bottom: 20px !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"]::before {
        content: "Aether Engine";
        display: block;
        font-size: 11px; font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.04em; text-transform: uppercase;
        margin-bottom: 8px;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) p,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) span,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) li {
        color: var(--text) !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li {
        color: var(--text);
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
        line-height: 1.6 !important;
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

    /* ---------- THINKING (linha fina) ---------- */
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
        font-weight: 400 !important;
        background: transparent !important;
        border: none !important;
        list-style: none !important;
        opacity: 0.75;
        transition: opacity 0.25s ease, color 0.25s ease;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary:hover {
        opacity: 1;
        color: var(--text-dim) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary p {
        font-size: 12px !important;
        color: inherit !important;
        display: inline !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary svg {
        width: 10px !important;
        height: 10px !important;
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
        opacity: 0.85;
    }

    /* ---------- COMPOSER (form) ---------- */
    [data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 8px 10px !important;
        box-shadow: var(--shadow-sm);
        margin-top: 8px;
    }
    [data-testid="stForm"] [data-testid="stVerticalBlock"] {
        gap: 6px !important;
    }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 4px !important;
    }

    /* Text input dentro do form */
    [data-testid="stForm"] [data-testid="stTextInput"] {
        background: transparent !important;
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
        font-size: 15px !important;
        padding: 10px 6px !important;
        height: 42px !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
        color: var(--text-mute) !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input:focus {
        box-shadow: none !important;
        border: none !important;
    }

    /* Icon buttons ao lado do input (HTML apenas decorativo) */
    .composer-icon {
        width: 38px; height: 38px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-mute);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .composer-icon:hover {
        background: var(--bg-2);
        color: var(--accent);
    }

    /* Submit button */
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        width: 42px !important;
        height: 42px !important;
        min-width: 42px !important;
        padding: 0 !important;
        font-size: 0 !important;
        box-shadow: 0 2px 6px rgba(201,100,66,.28) !important;
        transition: all 0.2s ease !important;
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
        background: #b85738 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(201,100,66,.35) !important;
    }

    /* ---------- PROGRESS PILL ---------- */
    .progress-pill {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 14px;
        background: var(--accent-soft);
        border: 1px solid rgba(201,100,66,.18);
        border-radius: var(--radius-pill);
        font-size: 12px; color: var(--accent);
        font-weight: 500;
        margin: 6px 0 10px 0;
        animation: fadeUp 0.3s ease;
    }
    .progress-pill .spark {
        display: inline-flex;
        animation: spin 2.2s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    .progress-track {
        flex: 1; height: 3px;
        background: rgba(201,100,66,.15);
        border-radius: 2px;
        overflow: hidden;
        margin-left: 4px;
    }
    .progress-fill {
        height: 100%;
        width: 35%;
        background: var(--accent);
        border-radius: 2px;
        animation: progressMove 1.4s ease-in-out infinite;
    }
    @keyframes progressMove {
        0%   { width: 15%; margin-left: 0%; }
        50%  { width: 45%; margin-left: 35%; }
        100% { width: 15%; margin-left: 85%; }
    }

    /* ---------- PREVIEW EMPTY STATE ---------- */
    .preview-empty {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        padding: 70px 30px;
        min-height: 420px;
    }
    .preview-empty-icon {
        width: 76px; height: 76px;
        display: flex; align-items: center; justify-content: center;
        background: var(--bg-2);
        border: 1px solid var(--border-soft);
        border-radius: 50%;
        color: var(--text-mute);
        margin-bottom: 20px;
    }
    .preview-empty-title {
        font-size: 16px; font-weight: 600;
        color: var(--text); margin-bottom: 8px;
        letter-spacing: -0.01em;
    }
    .preview-empty-text {
        font-size: 13px; color: var(--text-mute);
        line-height: 1.6; max-width: 300px;
        margin-bottom: 20px;
    }
    .preview-empty-btn {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 8px 16px;
        background: #ffffff;
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-size: 13px; font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }
    .preview-empty-btn:hover {
        border-color: var(--accent);
        color: var(--accent);
    }

    /* ---------- IFRAME ---------- */
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

    /* ---------- GENERAL BUTTONS ---------- */
    .stButton > button {
        background: #ffffff !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }

    /* ---------- MISC ---------- */
    hr { border-color: var(--border-soft) !important; margin: 1rem 0 !important; }
    .stAlert {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-2) !important;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #dedbd3; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #c9c6be; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "artifact_html" not in st.session_state:
    st.session_state.artifact_html = None
if "artifact_lang" not in st.session_state:
    st.session_state.artifact_lang = None
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


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
# TOP BAR
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
    <div class="topbar-menu">
      <div class="menu-btn" title="Configuracoes">{ICON_GEAR}</div>
      <div class="menu-btn" title="Projetos">{ICON_FOLDER}</div>
      <div class="menu-btn" title="Perfil">{ICON_USER}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LAYOUT — RAIL | CHAT | PREVIEW
# ============================================================
rail_col, chat_col, preview_col = st.columns([0.35, 1.15, 1], gap="small")


# ------------------------------------------------------------
# RAIL
# ------------------------------------------------------------
with rail_col:
    st.markdown(f"""
    <div class="rail">
      <div class="rail-btn primary" title="Nova conversa">{ICON_PLUS}</div>
      <div class="rail-divider"></div>
      <div class="rail-btn" title="Workspace">{ICON_SPARK}</div>
      <div class="rail-btn" title="Projetos">{ICON_FOLDER}</div>
      <div class="rail-spacer"></div>
      <div class="rail-divider"></div>
      <div class="rail-btn" title="Configuracoes">{ICON_GEAR}</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# CHAT
# ------------------------------------------------------------
with chat_col:

    st.markdown(
        '<div class="panel-label"><span>Conversa</span></div>',
        unsafe_allow_html=True,
    )

    chat_box = st.container(height=560)

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

    # ---- Composer ----
    with st.form("composer", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(
            [0.4, 6, 0.4, 0.85],
            gap="small",
            vertical_alignment="center",
        )
        with c1:
            st.markdown(
                f'<div class="composer-icon" title="Anexar arquivo">{ICON_CLIP}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            user_msg = st.text_input(
                "mensagem",
                placeholder="Envie uma mensagem para o Aether Engine...",
                label_visibility="collapsed",
            )
        with c3:
            st.markdown(
                f'<div class="composer-icon" title="Gravar audio">{ICON_MIC}</div>',
                unsafe_allow_html=True,
            )
        with c4:
            submitted = st.form_submit_button("Enviar")

    if submitted and user_msg.strip():
        st.session_state.pending_prompt = user_msg.strip()


# ------------------------------------------------------------
# PREVIEW
# ------------------------------------------------------------
with preview_col:

    st.markdown(f"""
    <div class="panel-label">
      <span>Preview</span>
      <div class="panel-label-tools">
        <div class="panel-tool" title="Atualizar">{ICON_REFRESH}</div>
        <div class="panel-tool" title="Zoom -">{ICON_ZOOM_OUT}</div>
        <div class="panel-tool" title="Zoom +">{ICON_ZOOM_IN}</div>
        <div class="panel-tool" title="Copiar codigo">{ICON_COPY}</div>
        <div class="panel-tool" title="Tela cheia">{ICON_FULL}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    preview_box = st.container(height=560)

    with preview_box:
        if st.session_state.artifact_html:
            components.html(st.session_state.artifact_html, height=530, scrolling=True)
        else:
            st.markdown(f"""
            <div class="preview-empty">
              <div class="preview-empty-icon">{ICON_IMAGE}</div>
              <div class="preview-empty-title">Seu preview aparecera aqui</div>
              <div class="preview-empty-text">
                Peca a IA para gerar uma interface, componente ou SVG.
                O resultado e renderizado em tempo real neste painel.
              </div>
              <div class="preview-empty-btn">Exemplo: landing page</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PROCESSAMENTO DO PROMPT
# ============================================================
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append({"role": "user", "content": prompt})

    with chat_col:
        # Re-renderiza a mensagem do usuario no topo da fila visual
        with st.chat_message("user", avatar=_AVATAR_USER):
            st.markdown(prompt)

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
                    temperature=1,
                    top_p=0.95,
                    max_tokens=8192,
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
                    st.session_state.artifact_html = parsed["artifact"]
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

    st.rerun()
