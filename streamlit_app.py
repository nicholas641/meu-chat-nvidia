import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIGURAÇÃO DA API NVIDIA
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="NVIDIA · Nemotron Chat",
    page_icon="🟩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS — PADRÃO NVIDIA INDUSTRIAL
# Regras: fundo preto sólido, cinza escuro secundário, bordas
# metálicas finas, cantos retos (6px max), sem sombras, sem
# gradientes em texto. Verde #76B900 apenas como acento.
# ============================================================
st.markdown("""
<style>
    /* ---------- RESET / BASE ---------- */
    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #b3b3b3;
    }

    .stApp {
        background-color: #0b0b0b;
    }

    /* Remove decoração padrão do Streamlit (header, footer) */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* ---------- TIPOGRAFIA ---------- */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    p, span, label, li {
        color: #b3b3b3;
    }
    a {
        color: #76B900;
        text-decoration: none;
    }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #252525;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    /* ---------- BLOCOS / CARDS / MENSAGENS ---------- */
    [data-testid="stChatMessage"] {
        background-color: #141414;
        border: 1px solid #252525;
        border-radius: 6px !important;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: none !important;
    }

    /* Borda de acento verde apenas no lado do assistente */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 2px solid #76B900;
    }

    /* ---------- BOTÕES ---------- */
    .stButton > button,
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background-color: #141414;
        color: #ffffff;
        border: 1px solid #252525;
        border-radius: 6px !important;
        font-weight: 600;
        padding: 0.55rem 1rem;
        transition: border-color 0.15s ease, color 0.15s ease;
        box-shadow: none !important;
    }
    .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #76B900;
        color: #76B900;
    }
    .stButton > button:focus:not(:active) {
        border-color: #76B900;
        color: #76B900;
        box-shadow: none !important;
    }

    /* Botão primário = verde sólido (ação destrutiva / principal) */
    .stButton > button[kind="primary"] {
        background-color: #76B900;
        color: #0b0b0b;
        border: 1px solid #76B900;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #8bcf1a;
        border-color: #8bcf1a;
        color: #0b0b0b;
    }

    /* ---------- EXPANDER (raciocínio da IA) ---------- */
    [data-testid="stExpander"] {
        background-color: #0e0e0e;
        border: 1px solid #252525;
        border-radius: 6px !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        color: #b3b3b3;
        font-weight: 600;
        font-size: 0.9rem;
    }
    [data-testid="stExpander"] summary:hover {
        color: #76B900;
    }

    /* ---------- INPUT DE CHAT ---------- */
    [data-testid="stChatInput"] {
        background-color: #141414;
        border: 1px solid #252525;
        border-radius: 6px !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #76B900;
    }
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #6a6a6a;
    }

    /* ---------- DIVISORES ---------- */
    hr {
        border-color: #252525 !important;
        margin: 1rem 0;
    }

    /* ---------- CURSOR DE DIGITAÇÃO ---------- */
    .typing-cursor {
        display: inline-block;
        color: #76B900;
        font-weight: 700;
        animation: blink 1s step-start infinite;
        margin-left: 2px;
    }
    @keyframes blink {
        50% { opacity: 0; }
    }

    /* ---------- BADGE / LABEL INDUSTRIAL ---------- */
    .nv-badge {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #76B900;
        border: 1px solid #252525;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 0.75rem;
    }

    /* ---------- RODAPÉ / META ---------- */
    .nv-meta {
        font-size: 0.78rem;
        color: #6a6a6a;
        letter-spacing: 0.02em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<span class="nv-badge">NVIDIA · NIM</span>', unsafe_allow_html=True)
    st.markdown("## Nemotron Chat")
    st.markdown('<span class="nv-meta">nvidia/nemotron-3-ultra-550b-a55b</span>', unsafe_allow_html=True)
    st.markdown("---")

    # Ação principal: limpar histórico
    if st.button("🗑️  Limpar Histórico", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.toast("Histórico limpo.", icon="✅")
        st.rerun()

    st.markdown("---")

    st.markdown("### Operação")
    st.markdown(
        """
        - Digite a consulta no campo inferior  
        - Resposta em streaming em tempo real  
        - Abra **Pensamento da IA** para auditar o raciocínio  
        """
    )

    st.markdown("---")

    st.markdown("### Parâmetros")
    st.markdown(
        f"""
        - **Modelo:** `{MODEL}`  
        - **Thinking:** habilitado  
        - **Temperature:** `1.0`  
        - **Top-p:** `0.95`  
        - **Max tokens:** `16384`  
        """
    )

    st.markdown("---")
    st.markdown('<span class="nv-meta">Streamlit · OpenAI SDK · NVIDIA NIM</span>', unsafe_allow_html=True)

# ============================================================
# CABEÇALHO
# ============================================================
st.markdown('<span class="nv-badge">Sessão ativa</span>', unsafe_allow_html=True)
st.markdown("# Nemotron-3-Ultra Chat")
st.markdown(
    '<span class="nv-meta">Console de conversação com raciocínio auditável em tempo real.</span>',
    unsafe_allow_html=True
)
st.markdown("---")

# ============================================================
# ESTADO
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# RENDER DO HISTÓRICO
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🟩"):
            if msg.get("reasoning"):
                with st.expander("🧠 Pensamento da IA", expanded=False):
                    st.markdown(msg["reasoning"])
            st.markdown(msg["content"])

# ============================================================
# INPUT + STREAMING
# ============================================================
if prompt := st.chat_input("Digite sua consulta..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🟩"):
        reasoning_box = st.expander("🧠 Pensamento da IA", expanded=False)
        with reasoning_box:
            reasoning_placeholder = st.empty()

        content_placeholder = st.empty()

        full_reasoning = ""
        full_content = ""

        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}},
                stream=True
            )

            for chunk in completion:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    full_reasoning += reasoning
                    reasoning_placeholder.markdown(
                        full_reasoning + '<span class="typing-cursor">▌</span>',
                        unsafe_allow_html=True
                    )

                if delta.content:
                    full_content += delta.content
                    content_placeholder.markdown(
                        full_content + '<span class="typing-cursor">▌</span>',
                        unsafe_allow_html=True
                    )

            # Render final (sem cursor)
            if full_reasoning:
                reasoning_placeholder.markdown(full_reasoning)
            content_placeholder.markdown(full_content if full_content else "_Sem resposta._")

        except Exception as e:
            st.error(f"Falha na chamada da API NVIDIA: {e}")
            full_content = f"Erro: {e}"

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_content,
            "reasoning": full_reasoning
        })
