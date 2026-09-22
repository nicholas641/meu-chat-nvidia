import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIGURAÇÃO DA API (conforme seu código original)
# ============================================================
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

# ============================================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Chat NVIDIA Nemotron",
    page_icon="🤖",
    layout="wide"
)
st.title("🤖 Chat com NVIDIA Nemotron-3-Ultra")
st.caption("Modelo: nvidia/nemotron-3-ultra-550b-a55b | Thinking habilitado")

# ============================================================
# GERENCIAMENTO DO HISTÓRICO DE CHAT (SESSION STATE)
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico na tela (recarregado a cada interação)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            # Se houver reasoning salvo no histórico, exibe em expander
            if msg.get("reasoning"):
                with st.expander("🧠 Raciocínio (thinking)"):
                    st.markdown(msg["reasoning"])
            st.markdown(msg["content"])

# ============================================================
# FUNÇÃO PRINCIPAL DE STREAMING
# ============================================================
def stream_nvidia_response(messages):
    """
    Envia o histórico para a API da NVIDIA e faz yield dos chunks
    conforme chegam. Retorna tuplas (tipo, texto):
    - ('reasoning', texto) para o pensamento
    - ('content', texto) para a resposta final
    """
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
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

        # O reasoning_content pode vir como atributo ou como None
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            yield ("reasoning", reasoning)

        if delta.content is not None:
            yield ("content", delta.content)


# ============================================================
# INTERFACE DE INPUT E CHAMADA À API
# ============================================================
if prompt := st.chat_input("Digite sua pergunta..."):
    # 1. Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Exibe imediatamente a mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Prepara a resposta do assistente
    with st.chat_message("assistant"):
        reasoning_placeholder = st.empty()
        content_placeholder = st.empty()

        full_reasoning = ""
        full_content = ""

        # Expander para o raciocínio (inicia vazio)
        with st.expander("🧠 Raciocínio (thinking)", expanded=True):
            reasoning_box = st.empty()

        # 4. Itera sobre o stream da API
        for kind, text in stream_nvidia_response(st.session_state.messages):
            if kind == "reasoning":
                full_reasoning += text
                reasoning_box.markdown(full_reasoning)
            elif kind == "content":
                full_content += text
                content_placeholder.markdown(full_content)

        # 5. Salva a resposta completa no histórico
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_content,
            "reasoning": full_reasoning
        })

        # 6. Força um rerun para que o histórico seja renderizado
        #    corretamente na próxima interação (opcional, mas evita duplicação visual)
        # st.rerun()  # Descomente se notar mensagens duplicadas na tela