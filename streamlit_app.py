import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIGURAÇÃO DA API NVIDIA (mesma do seu código original)
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Nemotron Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO (visual moderno estilo ChatGPT/Claude)
# ============================================================
st.markdown("""
<style>
    /* ---- Fonte e fundo geral ---- */
    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ---- Título principal com gradiente ---- */
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #76b900 0%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .main-subtitle {
        color: #8a8f98;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* ---- Bolhas de mensagem ---- */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    /* Mensagem do usuário - leve destaque azul */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(118, 185, 0, 0.05));
        border-left: 3px solid #00d4ff;
    }

    /* Mensagem do assistente - leve destaque verde */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, rgba(118, 185, 0, 0.08), rgba(0, 212, 255, 0.04));
        border-left: 3px solid #76b900;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d23 0%, #14161a 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #f0f2f5;
    }

    /* ---- Botão "Limpar Histórico" ---- */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        background: linear-gradient(90deg, #76b900, #5a8f00);
        color: white;
        border: none;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(118, 185, 0, 0.4);
        background: linear-gradient(90deg, #8bcf1a, #76b900);
    }

    /* ---- Expander do raciocínio ---- */
    [data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid rgba(118, 185, 0, 0.25);
        background: rgba(118, 185, 0, 0.04);
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        font-weight: 600;
        color: #a8d84a;
    }

    /* ---- Input de chat ---- */
    [data-testid="stChatInput"] textarea {
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background: #1e2127 !important;
    }

    /* ---- Cursor de digitação ---- */
    .typing-cursor {
        display: inline-block;
        color: #76b900;
        font-weight: 700;
        animation: blink 1s step-start infinite;
        margin-left: 2px;
    }
    @keyframes blink {
        50% { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🤖 Nemotron Chat")
    st.caption("Powered by NVIDIA NIM")
    st.markdown("---")

    # Botão limpar histórico
    if st.button("🗑️  Limpar Histórico", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.toast("Histórico limpo com sucesso!", icon="✅")
        st.rerun()

    st.markdown("---")

    # Instruções
    st.markdown("### 📖 Como usar")
    st.markdown(
        """
        1. Digite sua pergunta no campo abaixo  
        2. Aguarde a IA responder em tempo real  
        3. Clique em **🧠 Pensamento da IA** para ver o raciocínio  
        4. Use **Limpar Histórico** para começar do zero  
        """
    )

    st.markdown("---")

    # Configurações do modelo
    st.markdown("### ⚙️ Configurações")
    st.markdown(f"**Modelo:**  \n`{MODEL}`")
    st.markdown("**Thinking:** ✅ Ativado")
    st.markdown("**Temperature:** `1.0`")
    st.markdown("**Top-p:** `0.95`")
    st.markdown("**Max tokens:** `16.384`")

    st.markdown("---")
    st.caption("💡 Construído com Streamlit + OpenAI SDK")
    st.caption("🎨 Visual inspirado em ChatGPT & Claude")

# ============================================================
# CABEÇALHO PRINCIPAL
# ============================================================
st.markdown('<div class="main-title">💬 Nemotron-3-Ultra Chat</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Converse com o modelo mais avançado da NVIDIA — com raciocínio em tempo real.</div>',
    unsafe_allow_html=True
)

# ============================================================
# ESTADO DA SESSÃO
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# RENDERIZA HISTÓRICO (recarregado a cada interação)
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            if msg.get("reasoning"):
                with st.expander("🧠 Pensamento da IA...", expanded=False):
                    st.markdown(msg["reasoning"])
            st.markdown(msg["content"])

# ============================================================
# INPUT DO USUÁRIO
# ============================================================
if prompt := st.chat_input("Digite sua mensagem para a IA..."):

    # 1) Salva e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # 2) Prepara a área do assistente
    with st.chat_message("assistant", avatar="🤖"):
        # Expander do raciocínio (colapsado por padrão)
        reasoning_box = st.expander("🧠 Pensamento da IA...", expanded=False)
        with reasoning_box:
            reasoning_placeholder = st.empty()

        # Área da resposta final
        content_placeholder = st.empty()

        full_reasoning = ""
        full_content = ""

        # 3) Chama a API em modo streaming
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

                # Captura o raciocínio (reasoning_content)
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    full_reasoning += reasoning
                    reasoning_placeholder.markdown(
                        full_reasoning + '<span class="typing-cursor">▌</span>',
                        unsafe_allow_html=True
                    )

                # Captura o conteúdo final
                if delta.content:
                    full_content += delta.content
                    content_placeholder.markdown(
                        full_content + '<span class="typing-cursor">▌</span>',
                        unsafe_allow_html=True
                    )

            # 4) Renderização final (sem cursor piscando)
            if full_reasoning:
                reasoning_placeholder.markdown(full_reasoning)
            content_placeholder.markdown(full_content if full_content else "_Sem resposta._")

        except Exception as e:
            st.error(f"❌ Erro ao conectar com a API da NVIDIA:\n\n`{e}`")
            full_content = f"Ocorreu um erro: {e}"

        # 5) Salva a resposta completa no histórico
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_content,
            "reasoning": full_reasoning
        })
