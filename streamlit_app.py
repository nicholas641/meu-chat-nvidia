"""
streamlit_app.py
----------------
Chat com painel de Artifacts (estilo Claude Code) sob identidade visual NVIDIA.
Layout: duas colunas fixas — chat à esquerda, painel de artifact à direita.
Backend: NVIDIA NIM (nemotron-3-ultra) com thinking habilitado.

Para migrar para DeepSeek, basta substituir o bloco "NVIDIA NIM CLIENT"
por um OpenAI(base_url="https://api.deepseek.com", api_key="...") e ajustar
MODEL. O pipeline de parse (thinking/artifact) não muda.
"""

import re
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# ============================================================
# NVIDIA NIM CLIENT
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
)
MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


# ============================================================
# ARTIFACT PADRÃO (estado inicial do painel direito)
# ============================================================
DEFAULT_ARTIFACT = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin:0; padding:0; background:#0b0b0b; }
  body {
    font-family: "Inter","Segoe UI",-apple-system,sans-serif;
    color:#b3b3b3; padding:32px;
  }
  .box {
    border:1px solid #252525; background:#141414;
    border-radius:6px; padding:24px;
  }
  .tag {
    color:#76B900; font-size:10px; font-weight:700;
    letter-spacing:.12em; text-transform:uppercase;
  }
  h1 { color:#ffffff; font-size:16px; margin:8px 0; letter-spacing:-.01em; }
  p  { font-size:13px; line-height:1.6; margin:0; }
  code {
    font-family: "JetBrains Mono",Consolas,monospace;
    color:#76B900; font-size:12px;
  }
</style>
</head>
<body>
  <div class="box">
    <div class="tag">Artifact · Idle</div>
    <h1>Nenhum artefato renderizado</h1>
    <p>Peça à IA a geração de um componente HTML. Quando o modelo emitir um
       bloco <code>&lt;artifact&gt;...&lt;/artifact&gt;</code>, o preview
       aparecerá aqui automaticamente.</p>
  </div>
</body>
</html>
"""


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="NVIDIA · Artifacts Chat",
    page_icon="🟩",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS — IDENTIDADE NVIDIA INDUSTRIAL
# Regras: fundo #0b0b0b, blocos #141414, bordas #252525,
#         radius máximo 6px, zero sombras, acento #76B900.
# ============================================================
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
    }

    .stApp { background-color: #0b0b0b; }

    header[data-testid="stHeader"] { background: transparent; height: 0; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    .block-container {
        padding: 1.2rem 1.4rem 1rem 1.4rem !important;
        max-width: 100% !important;
    }

    /* ---------- TIPOGRAFIA ---------- */
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; letter-spacing: -0.01em; }
    p, span, label, li      { color: #b3b3b3; }
    a { color: #76B900; text-decoration: none; }

    /* ---------- LAYOUT DE COLUNAS ---------- */
    [data-testid="stHorizontalBlock"] { gap: 12px !important; }

    /* ---------- HEADER INDUSTRIAL ---------- */
    .nv-header {
        display: flex; align-items: center; justify-content: space-between;
        border: 1px solid #252525; background: #141414;
        border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;
    }
    .nv-header-left { display: flex; align-items: center; gap: 12px; }
    .nv-badge {
        font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #76B900;
        border: 1px solid #252525; padding: 3px 8px; border-radius: 4px;
    }
    .nv-title { color: #ffffff; font-size: 14px; font-weight: 700; }
    .nv-sub   { color: #6a6a6a; font-size: 11px; letter-spacing: 0.02em; }

    /* ---------- LABELS DE PAINEL ---------- */
    .panel-label {
        font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: #6a6a6a;
        padding: 2px 0 8px 0;
    }

    /* ---------- BOLHAS DE CHAT ---------- */
    [data-testid="stChatMessage"] {
        background-color: #141414 !important;
        border: 1px solid #252525;
        border-radius: 6px !important;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: none !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 2px solid #76B900;
    }

    /* ---------- INPUT DE CHAT ---------- */
    [data-testid="stChatInput"] {
        background-color: #141414;
        border: 1px solid #252525;
        border-radius: 6px !important;
    }
    [data-testid="stChatInput"]:focus-within { border-color: #76B900; }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #6a6a6a; }

    /* ---------- EXPANDER (THINKING) ---------- */
    [data-testid="stExpander"] {
        background-color: #0e0e0e !important;
        border: 1px solid #252525 !important;
        border-radius: 6px !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        color: #b3b3b3 !important;
        font-weight: 600; font-size: 0.85rem;
    }
    [data-testid="stExpander"] summary:hover { color: #76B900 !important; }

    /* ---------- TABS DO PAINEL DE ARTIFACT ---------- */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid #252525;
        gap: 0;
    }
    [data-testid="stTabs"] [role="tab"] {
        color: #6a6a6a;
        font-size: 11px; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase;
        padding: 8px 14px; border-radius: 0;
        background: transparent;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #ffffff;
        background: #141414;
        border-bottom: 2px solid #76B900;
    }
    [data-testid="stTabs"] [role="tab"]:hover { color: #76B900; }

    /* ---------- st.code ---------- */
    [data-testid="stCode"] {
        border: 1px solid #252525 !important;
        border-radius: 6px !important;
        background: #0e0e0e !important;
    }
    [data-testid="stCode"] pre {
        background: #0e0e0e !important;
        border-radius: 6px !important;
    }

    /* ---------- BOTÕES ---------- */
    .stButton > button {
        background-color: #141414;
        color: #ffffff;
        border: 1px solid #252525;
        border-radius: 6px !important;
        font-weight: 600; font-size: 12px;
        padding: 0.4rem 0.9rem;
        box-shadow: none !important;
        transition: border-color 0.15s ease, color 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #76B900;
        color: #76B900;
    }

    /* ---------- DIVISORES ---------- */
    hr { border-color: #252525 !important; }

    /* ---------- CURSOR DE DIGITAÇÃO ---------- */
    .typing-cursor {
        display: inline-block;
        color: #76B900;
        font-weight: 700;
        animation: blink 1s step-start infinite;
        margin-left: 2px;
    }
    @keyframes blink { 50% { opacity: 0; } }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []           # [{role, content, thinking}]

if "artifact_code" not in st.session_state:
    st.session_state.artifact_code = DEFAULT_ARTIFACT

if "artifact_lang" not in st.session_state:
    st.session_state.artifact_lang = "html"


# ============================================================
# PARSERS (thinking + artifact)
# ============================================================
_THINK_RE    = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_ARTIFACT_RE = re.compile(r"<artifact(?:\s+[^>]*)?>(.*?)</artifact>", re.DOTALL | re.IGNORECASE)

# Remove tags abertas sem fechamento durante o streaming parcial.
_OPEN_TAG_RE = re.compile(r"<(thinking|artifact)\b[^>]*>(?![^<]*</\1>)", re.IGNORECASE)


def _strip_dangling_tags(text: str) -> str:
    """Remove tags <thinking>/<artifact> que ainda não foram fechadas."""
    return _OPEN_TAG_RE.sub("", text)


def extract_thinking(text: str) -> tuple[str, str]:
    """Retorna (texto_sem_thinking, thinking_concatenado)."""
    blocks = _THINK_RE.findall(text)
    thinking = "\n\n".join(b.strip() for b in blocks)
    visible = _THINK_RE.sub("", text)
    return visible.strip(), thinking.strip()


def extract_artifact(text: str) -> tuple[str, str | None]:
    """Retorna (texto_sem_artifact, primeiro_artifact ou None)."""
    match = _ARTIFACT_RE.search(text)
    artifact = match.group(1).strip() if match else None
    visible = _ARTIFACT_RE.sub("", text)
    return visible.strip(), artifact


def parse_response(raw: str) -> dict:
    """Pipeline: separa artifact, thinking e texto visível final."""
    without_artifact, artifact = extract_artifact(raw)
    without_thinking, thinking = extract_thinking(without_artifact)
    return {
        "text":     without_thinking,
        "thinking": thinking,
        "artifact": artifact,
    }


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="nv-header">
  <div class="nv-header-left">
    <span class="nv-badge">NVIDIA · NIM</span>
    <div>
      <div class="nv-title">Artifacts Chat</div>
      <div class="nv-sub">nvidia/nemotron-3-ultra-550b-a55b · thinking habilitado</div>
    </div>
  </div>
  <div class="nv-sub">two-column layout · artifact panel</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# LAYOUT: DUAS COLUNAS FIXAS
# A coluna direita é declarada primeiro para expor os placeholders
# (preview_slot / code_slot) no escopo do bloco de streaming.
# ============================================================
col_chat, col_artifact = st.columns([1.15, 1], gap="medium")


# ------------------------------------------------------------
# COLUNA DIREITA — PAINEL DE ARTIFACT
# ------------------------------------------------------------
with col_artifact:
    st.markdown('<div class="panel-label">Artifact Panel</div>', unsafe_allow_html=True)

    tab_preview, tab_code = st.tabs(["Live Preview", "Code Source"])

    with tab_preview:
        preview_slot = st.empty()
        with preview_slot:
            components.html(st.session_state.artifact_code, height=620, scrolling=True)

    with tab_code:
        code_slot = st.empty()
        code_slot.code(st.session_state.artifact_code, language=st.session_state.artifact_lang)

    # Utilitários
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Resetar Artifact", use_container_width=True):
            st.session_state.artifact_code = DEFAULT_ARTIFACT
            st.session_state.artifact_lang = "html"
            st.rerun()
    with c2:
        st.markdown(
            f'<div class="nv-sub" style="padding-top:10px;text-align:right;">'
            f'lang: {st.session_state.artifact_lang} · '
            f'bytes: {len(st.session_state.artifact_code)}</div>',
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------
# COLUNA ESQUERDA — CHAT
# ------------------------------------------------------------
with col_chat:
    st.markdown('<div class="panel-label">Conversa</div>', unsafe_allow_html=True)

    # ---- Renderiza histórico ----
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🟩"):
                if msg.get("thinking"):
                    with st.expander("🧠 Pensamento da IA", expanded=False):
                        st.markdown(msg["thinking"])
                st.markdown(msg["content"])

    # ---- Input ----
    if prompt := st.chat_input("Envie uma mensagem. Peça um artefato HTML para vê-lo no painel à direita..."):

        # 1) Persiste + exibe mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # 2) Área do assistente
        with st.chat_message("assistant", avatar="🟩"):
            thinking_slot = st.expander("🧠 Pensamento da IA", expanded=False)
            with thinking_slot:
                thinking_body = st.empty()

            text_body = st.empty()

            raw_buffer       = ""
            reasoning_accum  = ""

            try:
                # ============================================================
                # PONTO DE INTEGRAÇÃO DA API
                # ------------------------------------------------------------
                # Para migrar para DeepSeek:
                #   client = OpenAI(base_url="https://api.deepseek.com",
                #                   api_key="sk-...")
                #   MODEL  = "deepseek-reasoner"
                #   extra_body={"chat_template_kwargs":{"enable_thinking":True}} -> remover
                # O pipeline de parse abaixo (thinking/artifact) permanece igual.
                # ============================================================
                completion = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                    temperature=1,
                    top_p=0.95,
                    max_tokens=16384,
                    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
                    stream=True,
                )

                for chunk in completion:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    # Canal 1: reasoning_content nativo (Nemotron enable_thinking)
                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning:
                        reasoning_accum += reasoning
                        thinking_body.markdown(
                            reasoning_accum + '<span class="typing-cursor">▌</span>',
                            unsafe_allow_html=True,
                        )

                    # Canal 2: content principal — pode conter tags
                    if delta.content:
                        raw_buffer += delta.content

                        # Parse parcial para exibição incremental segura
                        partial_visible, partial_think = extract_thinking(raw_buffer)
                        partial_visible, _             = extract_artifact(partial_visible)
                        partial_visible                = _strip_dangling_tags(partial_visible)

                        combined_think = "\n\n".join(
                            filter(None, [reasoning_accum, partial_think])
                        )
                        if combined_think:
                            thinking_body.markdown(
                                combined_think + '<span class="typing-cursor">▌</span>',
                                unsafe_allow_html=True,
                            )
                        if partial_visible:
                            text_body.markdown(
                                partial_visible + '<span class="typing-cursor">▌</span>',
                                unsafe_allow_html=True,
                            )

                # 3) Parse final do buffer completo
                parsed = parse_response(raw_buffer)

                final_thinking = "\n\n".join(
                    filter(None, [reasoning_accum, parsed["thinking"]])
                )

                if final_thinking:
                    thinking_body.markdown(final_thinking)
                else:
                    thinking_body.markdown("_Sem raciocínio exposto._")

                text_body.markdown(parsed["text"] or "_Sem resposta._")

                # 4) Se veio artifact, atualiza painel direito
                if parsed["artifact"]:
                    st.session_state.artifact_code = parsed["artifact"]
                    st.session_state.artifact_lang = "html"

                    with preview_slot:
                        components.html(parsed["artifact"], height=620, scrolling=True)
                    code_slot.code(parsed["artifact"], language="html")

                # 5) Persiste resposta no histórico
                st.session_state.messages.append({
                    "role":     "assistant",
                    "content":  parsed["text"],
                    "thinking": final_thinking,
                })

            except Exception as e:
                st.error(f"Falha na API NVIDIA: {e}")
                st.session_state.messages.append({
                    "role":     "assistant",
                    "content":  f"Erro ao processar resposta: {e}",
                    "thinking": "",
                })
