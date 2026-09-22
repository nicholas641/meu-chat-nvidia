"""
Aether Engine
-------------
Chat com artifacts em tempo real. Visual inspirado no Claude (Anthropic).
Mensagens alinhadas a esquerda, fluxo continuo, input flutuante em pilula.
"""

import os
import re
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ============================================================
# API KEY — st.secrets > env var
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


# ============================================================
# CLIENT
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=_load_api_key(),
)
MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


# ============================================================
# AVATARES (invisiveis na UI, mantidos para targeting CSS)
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
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are Aether Engine, a professional technical assistant.

Strict rules:
1. Never use emojis or emoticons in your responses.
2. Be concise, technical, and direct. No filler, no friendly slang.
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
# CSS — ESTETICA CLAUDE (light mode off-white)
# ============================================================
st.markdown("""
<style>
    /* ---------- HIDE STREAMLIT CHROME ---------- */
    #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
    footer { display: none !important; visibility: hidden; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stDeployButton"] { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stAppDeployButton"] { display: none !important; }

    /* ---------- TOKENS ---------- */
    :root {
        --bg:           #fbfaf7;
        --bg-panel:     #f5f3ee;
        --bg-user:      #f0eee6;
        --bg-code:      #f5f3ee;
        --border:       #e8e5dd;
        --border-soft:  #efece4;
        --text:         #1a1a1a;
        --text-dim:     #6b6b6b;
        --text-mute:    #9a9388;
        --accent:       #c96442;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: var(--text);
        font-feature-settings: "ss01", "cv11";
        -webkit-font-smoothing: antialiased;
    }

    /* ---------- FUNDO SOLIDO (sem padrao) ---------- */
    .stApp { background-color: var(--bg); }

    .block-container {
        padding: 1.4rem 2rem 8rem 2rem !important;
        max-width: 100% !important;
    }

    /* ---------- TIPOGRAFIA ---------- */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text) !important;
        letter-spacing: -0.015em;
        font-weight: 500;
    }
    p, span, li, label { color: var(--text); font-size: 15px; line-height: 1.65; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ---------- HEADER ---------- */
    .ae-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 0 1rem 0;
        border-bottom: 1px solid var(--border-soft);
        margin-bottom: 1.4rem;
    }
    .ae-brand {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 19px; font-weight: 500; color: var(--text);
        letter-spacing: -0.02em;
    }
    .ae-brand-sub {
        font-size: 12px; color: var(--text-mute);
        margin-left: 10px; letter-spacing: 0.01em;
    }
    .ae-status {
        font-size: 11px; color: var(--text-mute);
        letter-spacing: 0.05em;
    }

    /* ============================================================
       CHAT MESSAGES — fluxo continuo, alinhado a esquerda
       ============================================================ */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 6px 0 !important;
        margin-bottom: 4px !important;
        box-shadow: none !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: flex-start !important;
        gap: 0 !important;
        animation: ae-fade 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Esconde os avatares (mantidos no DOM apenas para selectors :has) */
    [data-testid="stChatMessage"] img {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Content container base */
    [data-testid="stChatMessageContent"] {
        flex: 1 1 auto !important;
        max-width: 100% !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
    }

    /* ---------- USER — bubble leve bege, alinhada a esquerda ---------- */
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) {
        margin-bottom: 16px !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) [data-testid="stChatMessageContent"] {
        background: var(--bg-user) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
        max-width: 78% !important;
        flex: 0 1 auto !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) p,
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) span,
    [data-testid="stChatMessage"]:has(img[src*="useravatar"]) li {
        color: var(--text) !important;
    }

    /* ---------- ASSISTANT — sem bubble, texto fluido ---------- */
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) {
        margin-bottom: 22px !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"] {
        padding: 0 0 0 0 !important;
    }
    /* Label discreto acima da resposta do assistente */
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"]::before {
        content: "Aether Engine";
        display: block;
        font-size: 12px;
        color: var(--text-mute);
        font-weight: 500;
        letter-spacing: 0.01em;
        margin-bottom: 6px;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) p,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) span,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) li {
        color: var(--text) !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
    }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) h1,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) h2,
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) h3 {
        color: var(--text) !important;
        margin-top: 1rem !important;
    }

    @keyframes ae-fade {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ============================================================
       CODE BLOCKS — padrao Claude (fundo claro, texto escuro)
       ============================================================ */
    [data-testid="stChatMessage"] [data-testid="stCode"],
    [data-testid="stChatMessage"] pre {
        background: var(--bg-code) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
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

    /* ============================================================
       THINKING — linha fina, discreta, quase imperceptivel
       ============================================================ */
    [data-testid="stChatMessage"] [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        border-radius: 0 !important;
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
        letter-spacing: 0.01em;
        background: transparent !important;
        border: none !important;
        list-style: none !important;
        opacity: 0.7;
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
        opacity: 0.6;
        margin-right: 6px;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {
        border-left: 1px solid var(--border) !important;
        padding: 6px 0 6px 14px !important;
        margin: 6px 0 12px 0 !important;
        background: transparent !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] p {
        font-size: 13px !important;
        color: var(--text-dim) !important;
        line-height: 1.65;
        font-style: italic;
        opacity: 0.85;
    }

    /* ============================================================
       CHAT INPUT — pilula flutuante, centrada
       ============================================================ */
    [data-testid="stChatInput"] {
        max-width: 720px !important;
        margin: 0 auto !important;
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 999px !important;
        padding: 4px 8px !important;
        box-shadow:
            0 4px 16px rgba(0, 0, 0, 0.05),
            0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow:
            0 4px 20px rgba(201, 100, 66, 0.10),
            0 0 0 3px rgba(201, 100, 66, 0.08) !important;
    }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--text) !important;
        font-size: 15px !important;
        padding: 8px 12px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-mute) !important;
    }
    [data-testid="stChatInput"] button {
        background: var(--text) !important;
        color: var(--bg) !important;
        border-radius: 999px !important;
    }

    /* ============================================================
       BOTOES GERAIS
       ============================================================ */
    .stButton > button {
        background: transparent !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.4rem 0.9rem !important;
        transition: all 0.25s ease-in-out !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201, 100, 66, 0.04) !important;
    }

    /* ============================================================
       ARTIFACT PANEL
       ============================================================ */
    .ae-panel-header {
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-soft);
        margin-bottom: 14px;
    }
    .ae-panel-title {
        font-size: 12px; color: var(--text-dim);
        font-weight: 500; letter-spacing: 0.02em;
    }
    .ae-panel-meta {
        font-size: 11px; color: var(--text-mute);
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        letter-spacing: 0.02em;
    }

    iframe {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        background: #ffffff !important;
    }

    .ae-empty {
        border: 1px dashed var(--border);
        border-radius: 10px;
        padding: 60px 24px;
        text-align: center;
        background: var(--bg-panel);
    }
    .ae-empty-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 16px; color: var(--text-dim);
        margin-bottom: 8px; font-weight: 500;
    }
    .ae-empty-text {
        font-size: 13px; color: var(--text-mute);
        line-height: 1.6; max-width: 320px; margin: 0 auto;
    }

    /* ---------- TYPING CURSOR ---------- */
    .ae-cursor {
        display: inline-block;
        width: 2px; height: 1.05em;
        background: var(--text);
        vertical-align: text-bottom;
        margin-left: 2px;
        animation: ae-blink 1s step-start infinite;
        opacity: 0.7;
    }
    @keyframes ae-blink { 50% { opacity: 0; } }

    /* ---------- MISC ---------- */
    hr { border-color: var(--border-soft) !important; margin: 1rem 0 !important; }

    [data-testid="stCode"] {
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
    }

    .stAlert {
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-panel) !important;
        color: var(--text) !important;
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


# ============================================================
# EMOJI SANITIZER
# ============================================================
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U0001F700-\U0001F77F"
    "\U0000FE00-\U0000FE0F"
    "\U00002B00-\U00002BFF"
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


# ============================================================
# PARSING
# ============================================================
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
    low = code.lower()
    if "<svg" in low and "<html" not in low:
        return "svg"
    return "html"


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
# HEADER
# ============================================================
st.markdown("""
<div class="ae-header">
  <div style="display:flex; align-items:baseline;">
    <span class="ae-brand">Aether Engine</span>
    <span class="ae-brand-sub">conversational workspace</span>
  </div>
  <div class="ae-status">online</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LAYOUT
# ============================================================
col_chat, col_preview = st.columns([1.35, 1], gap="large")


# ------------------------------------------------------------
# COLUNA DIREITA — PREVIEW
# ------------------------------------------------------------
with col_preview:
    st.markdown("""
    <div class="ae-panel-header">
      <span class="ae-panel-title">Preview</span>
      <span class="ae-panel-meta">live render</span>
    </div>
    """, unsafe_allow_html=True)

    preview_slot = st.empty()

    if st.session_state.artifact_html:
        with preview_slot:
            components.html(st.session_state.artifact_html, height=680, scrolling=True)
    else:
        preview_slot.markdown("""
        <div class="ae-empty">
          <div class="ae-empty-title">Nada renderizado</div>
          <div class="ae-empty-text">
            Peca a IA para gerar uma interface, componente ou SVG.
            O resultado aparece aqui em tempo real.
          </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------
# COLUNA ESQUERDA — CHAT
# ------------------------------------------------------------
with col_chat:

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

    if prompt := st.chat_input("Envie uma mensagem..."):

        st.session_state.messages.append({"role": "user", "content": prompt})
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
                            reasoning_accum + '<span class="ae-cursor"></span>',
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
                                combined + '<span class="ae-cursor"></span>',
                                unsafe_allow_html=True,
                            )
                        if partial_visible:
                            text_body.markdown(
                                partial_visible + '<span class="ae-cursor"></span>',
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
                    with preview_slot:
                        components.html(parsed["artifact"], height=680, scrolling=True)

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
