"""
Aether Engine
-------------
Workspace conversacional com renderizacao de artifacts em tempo real.
Interface inspirada em sistemas modernos de chat com painel de preview.
"""

import re
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ============================================================
# CLIENT
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


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
# CSS — PALETA E ESTETICA CLAUDE
# Esconde o Streamlit, aplica paleta off-white, tipografia serif,
# animacoes suaves, barra de pensamento discreta, cursor de digitacao.
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
        --bg:          #fbfaf7;
        --bg-panel:    #f5f4ed;
        --bg-bubble:   #f0eee6;
        --border:      #e8e6de;
        --border-soft: #efece4;
        --text:        #1a1a1a;
        --text-dim:    #6b6b6b;
        --text-mute:   #9a9a9a;
        --accent:      #c96442;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: var(--text);
        font-feature-settings: "ss01", "cv11";
    }

    .stApp { background: var(--bg); }

    .block-container {
        padding: 1.5rem 2rem 6rem 2rem !important;
        max-width: 100% !important;
    }

    /* ---------- TYPOGRAPHY ---------- */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text) !important;
        letter-spacing: -0.02em;
        font-weight: 500;
    }
    p, span, li, label {
        color: var(--text);
        font-size: 15px;
        line-height: 1.65;
    }
    a { color: var(--accent); text-decoration: none; }

    /* ---------- BRAND HEADER ---------- */
    .ae-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.25rem 0 1.1rem 0;
        border-bottom: 1px solid var(--border-soft);
        margin-bottom: 1.5rem;
    }
    .ae-brand {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 22px;
        font-weight: 500;
        color: var(--text);
        letter-spacing: -0.02em;
    }
    .ae-brand-sub {
        font-size: 12px;
        color: var(--text-mute);
        margin-left: 12px;
        letter-spacing: 0.02em;
    }
    .ae-status {
        font-size: 11px;
        color: var(--text-mute);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* ---------- CHAT MESSAGES ---------- */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 10px 0 !important;
        margin-bottom: 10px !important;
        box-shadow: none !important;
        animation: ae-fade-up 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: var(--bg-bubble) !important;
        border-radius: 14px !important;
        padding: 12px 18px !important;
        margin-left: 18% !important;
        border: 1px solid var(--border-soft) !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        padding-left: 0 !important;
    }

    [data-testid="chatAvatarIcon-user"],
    [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }
    [data-testid="stChatMessage"] > img {
        display: none !important;
    }

    @keyframes ae-fade-up {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ---------- THINKING BAR ---------- */
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        border-radius: 0 !important;
        margin-bottom: 6px !important;
    }
    [data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stExpander"] summary {
        padding: 4px 0 !important;
        font-size: 12px !important;
        color: var(--text-mute) !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em;
        transition: color 0.3s ease-in-out;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: var(--text-dim) !important;
    }
    [data-testid="stExpander"] summary p {
        font-size: 12px !important;
        color: inherit !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        border-left: 2px solid var(--border-soft);
        padding: 8px 0 8px 14px !important;
        margin: 4px 0 12px 2px !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
        font-size: 13px !important;
        color: var(--text-dim) !important;
        line-height: 1.6;
        font-style: italic;
    }

    /* ---------- CHAT INPUT ---------- */
    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(201,100,66,0.08) !important;
    }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--text) !important;
        font-size: 15px !important;
        border-radius: 14px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-mute) !important;
    }

    /* ---------- BUTTONS ---------- */
    .stButton > button {
        background: transparent !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 0.4rem 0.9rem !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,0.04) !important;
    }

    /* ---------- ARTIFACT PANEL ---------- */
    .ae-panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-soft);
        margin-bottom: 14px;
    }
    .ae-panel-title {
        font-size: 12px;
        color: var(--text-dim);
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .ae-panel-meta {
        font-size: 11px;
        color: var(--text-mute);
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
    }

    iframe {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        background: #ffffff !important;
        transition: all 0.3s ease-in-out;
    }

    .ae-empty {
        border: 1px dashed var(--border);
        border-radius: 12px;
        padding: 60px 24px;
        text-align: center;
        background: var(--bg-panel);
    }
    .ae-empty-title {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 17px;
        color: var(--text);
        margin-bottom: 8px;
        font-weight: 500;
    }
    .ae-empty-text {
        font-size: 13px;
        color: var(--text-mute);
        line-height: 1.6;
        max-width: 340px;
        margin: 0 auto;
    }

    /* ---------- TYPING CURSOR ---------- */
    .ae-cursor {
        display: inline-block;
        width: 2px;
        height: 1em;
        background: var(--text);
        vertical-align: text-bottom;
        margin-left: 2px;
        animation: ae-blink 1s step-start infinite;
    }
    @keyframes ae-blink {
        50% { opacity: 0; }
    }

    /* ---------- MISC ---------- */
    hr { border-color: var(--border-soft) !important; margin: 1rem 0 !important; }

    [data-testid="stCode"] {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
    }

    .stAlert {
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-mute); }
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
# PARSING — thinking, artifact, sanitizacao de stream parcial
# ============================================================
_THINK_RE     = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_ARTIFACT_RE  = re.compile(r"<artifact[^>]*>(.*?)</artifact>", re.DOTALL | re.IGNORECASE)
_HTML_BLOCK   = re.compile(r"```html\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_SVG_BLOCK    = re.compile(r"```svg\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_DANGLING_RE  = re.compile(r"<(thinking|artifact)\b[^>]*>(?![^<]*</\1>)", re.IGNORECASE)


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
    """Retorna (texto_limpo, artifact_html_ou_None, linguagem_ou_None)."""
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
        "text":     visible,
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
  <div class="ae-status">preview enabled</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LAYOUT — DUAS COLUNAS
# ============================================================
col_chat, col_preview = st.columns([1, 1], gap="large")


# ------------------------------------------------------------
# COLUNA DIREITA — ARTIFACT PREVIEW
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
          <div class="ae-empty-title">Nada para visualizar ainda</div>
          <div class="ae-empty-text">
            Peca a IA para criar uma interface, um componente ou um SVG.
            O resultado aparecera aqui automaticamente, em tempo real.
          </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------
# COLUNA ESQUERDA — CHAT
# ------------------------------------------------------------
with col_chat:

    # ---- Historico ----
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                if msg.get("thinking"):
                    with st.expander("Processando raciocinio..."):
                        st.markdown(msg["thinking"])
                if msg.get("content"):
                    st.markdown(msg["content"])

    # ---- Input + streaming ----
    if prompt := st.chat_input("Envie uma mensagem para o Aether Engine..."):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            thinking_slot = st.expander("Processando raciocinio...", expanded=False)
            with thinking_slot:
                thinking_body = st.empty()

            text_body = st.empty()

            raw_buffer = ""
            reasoning_accum = ""

            try:
                # ============================================================
                # API CALL — streaming
                # ============================================================
                completion = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
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

                    # Canal 1: reasoning_content nativo
                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning:
                        reasoning_accum += reasoning
                        thinking_body.markdown(
                            reasoning_accum + '<span class="ae-cursor"></span>',
                            unsafe_allow_html=True,
                        )

                    # Canal 2: content principal
                    if delta.content:
                        raw_buffer += delta.content

                        # Parse parcial para exibicao incremental segura
                        partial_visible, partial_think = extract_thinking(raw_buffer)
                        partial_visible, _, _ = extract_artifact(partial_visible)
                        partial_visible = _strip_dangling(partial_visible)

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

                # ---- Parse final ----
                parsed = parse_response(raw_buffer)
                final_thinking = "\n\n".join(
                    filter(None, [reasoning_accum, parsed["thinking"]])
                )

                if final_thinking:
                    thinking_body.markdown(final_thinking)
                else:
                    thinking_body.markdown("_Sem raciocinio exposto._")

                text_body.markdown(parsed["text"] or "_Sem resposta._")

                # ---- Atualiza painel de artifact ----
                if parsed["artifact"]:
                    st.session_state.artifact_html = parsed["artifact"]
                    st.session_state.artifact_lang = parsed["lang"]
                    with preview_slot:
                        components.html(parsed["artifact"], height=680, scrolling=True)

                # ---- Persiste no historico ----
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
