"""
Aether Engine — AI workspace
-----------------------------
Layout: sidebar nativa + header + 2 colunas (chat | preview).
Chat com historico/projetos/configuracoes funcionais.
Preview com file tree + raciocinio da IA (estilo "Arena").
"""

import os
import re
import urllib.parse
import pickle  # Adicionado para salvar as configurações
from datetime import datetime
import uuid

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# Funções automáticas de persistência de dados
def salvar_historico_no_disco():
    with open("backup_chat.pkl", "wb") as f:
        pickle.dump(st.session_state.messages, f)

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
ICON_IMAGE   = _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>', 44)
ICON_MIC     = _svg('<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/>', 18)
ICON_TRASH   = _svg('<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>', 16)
ICON_DOWNLOAD= _svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>', 14)
ICON_EDIT    = _svg('<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z"/>', 15)
ICON_STOP    = _svg('<rect x="6" y="6" width="12" height="12" rx="2"/>', 14)
ICON_BACK    = _svg('<path d="M15 18l-6-6 6-6"/>', 14)
ICON_NEXT    = _svg('<path d="M9 18l6-6-6-6"/>', 14)
ICON_EYE     = _svg('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>', 15)
ICON_CODE    = _svg('<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>', 15)
ICON_STAR    = _svg('<polygon points="12 2 15 9 22 9.3 16.5 14 18.5 21 12 17 5.5 21 7.5 14 2 9.3 9 9"/>', 14)
ICON_ARROWL  = _svg('<path d="M19 12H5M12 19l-7-7 7-7"/>', 15)


# ============================================================
# SYSTEM PROMPT (base + personalizacao definida pelo usuario)
# ============================================================
BASE_SYSTEM_PROMPT = """You are Aether Engine, a professional technical assistant.

Strict rules:
1. Be concise and direct.
2. Respond in the same language the user writes in.
3. When the user requests a UI component, visual, animation, or HTML/CSS/JS
   output, wrap the complete code inside <artifact>...</artifact> tags.
4. Inside <artifact>, either:
   a) write one full standalone HTML document (with <!DOCTYPE html>), or
   b) split it into multiple files using this format, when it makes sense
      for the request (e.g. a small app with separate structure):
      <file name="index.html">...</file>
      <file name="style.css">...</file>
      <file name="script.js">...</file>
      One of the files must be named index.html and must be a full HTML
      document (it can reference the css/js conceptually; they will be
      inlined automatically for preview).
5. Before or while producing the artifact, briefly narrate what you are
   doing in plain text outside the tags (e.g. "Lendo o pedido, vou criar
   index.html e style.css...") so the user can follow your reasoning.
6. Do not add commentary about the artifact outside the tags beyond a
   short summary.
"""


def build_system_prompt() -> str:
    prompt = BASE_SYSTEM_PROMPT
    custom = (st.session_state.get("custom_instructions") or "").strip()
    if custom:
        prompt += (
            "\n\nUser personalization instructions (ALWAYS follow these, "
            "they override the default tone/style, even rule 1 about being "
            "purely technical if they conflict):\n" + custom
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
    "messages":         carregar_historico_do_disco(),  # Agora carrega do arquivo salvo!
    "current_artifact": None,
    "artifact_lang":    None,
    "pending_prompt":   None,
    "temperature":      1.0,
    "top_p":            0.95,
    "max_tokens":       8192,
    "attached_name":    None,
    "attached_text":    None,
    "editing_idx":          None,  # indice de mensagem sendo editada
    "stop_requested":       False,
    "search_query":         "",
    "refresh_counter":      0,
    "custom_instructions":  "",   # personalizacao/memoria definida pelo usuario
    "conversations":        [],   # historico/projetos salvos
    "show_history":         False,
    "show_projects":        False,
    "show_settings":        False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# HELPERS DE CONVERSA (usados pelo router)
# ============================================================
def _reset_conversation():
    st.session_state.messages = []
    st.session_state.current_artifact = None
    st.session_state.current_files = {}
    st.session_state.current_thinking = ""
    st.session_state.artifact_lang = None
    st.session_state.artifact_versions = []
    st.session_state.artifact_version_idx = -1
    st.session_state.artifact_edit_mode = False
    st.session_state.preview_view = "preview"
    st.session_state.selected_file = None
    st.session_state.editing_idx = None


def _close_panels():
    st.session_state.show_history = False
    st.session_state.show_projects = False
    st.session_state.show_settings = False


def _snapshot_conversation(pinned: bool = False, title: str = None):
    """Salva a conversa atual (se tiver mensagens) na lista de conversas."""
    if not st.session_state.messages:
        return
    if title is None:
        first_user = next(
            (m["content"] for m in st.session_state.messages if m["role"] == "user"),
            "Conversa",
        )
        title = (first_user or "Conversa").strip().splitlines()[0][:42]
    st.session_state.conversations.insert(0, {
        "id":                   str(uuid.uuid4())[:8],
        "title":                title or "Conversa sem titulo",
        "ts":                   datetime.now().strftime("%d/%m %H:%M"),
                "messages":             st.session_state.messages,
        "artifact_versions":    st.session_state.get("artifact_versions", []),
        "artifact_version_idx": st.session_state.get("artifact_version_idx", -1),
        "current_artifact":     st.session_state.get("current_artifact", None),
        "current_files":        st.session_state.get("current_files", {}),
        "current_thinking":     st.session_state.get("current_thinking", ""),
        "artifact_lang":        st.session_state.get("artifact_lang", None),
        "pinned":               pinned,
    })


def _load_conversation(conv_id: str) -> bool:
    for c in st.session_state.conversations:
        if c["id"] == conv_id:
            st.session_state.messages             = c["messages"]
            st.session_state.artifact_versions     = c["artifact_versions"]
            st.session_state.artifact_version_idx  = c["artifact_version_idx"]
            st.session_state.current_artifact      = c["current_artifact"]
            st.session_state.current_files         = c.get("current_files", {})
            st.session_state.current_thinking      = c.get("current_thinking", "")
            st.session_state.artifact_lang         = c["artifact_lang"]
            st.session_state.artifact_edit_mode    = False
            st.session_state.preview_view          = "preview"
            st.session_state.editing_idx           = None
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

    elif _action == "refresh":
        # Contador injetado no HTML do preview para forcar o navegador a
        # remontar o iframe de verdade (JS/timers/estado reiniciam).
        st.session_state.refresh_counter += 1
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
        st.session_state.current_artifact = None
        if os.path.exists("backup_chat.pkl"):
            os.remove("backup_chat.pkl")
        st.rerun()


    # ---- Navegacao de versoes do artifact ----
    elif _action == "artifact_prev":
        if st.session_state.artifact_versions:
            i = st.session_state.artifact_version_idx - 1
            if i < 0:
                i = len(st.session_state.artifact_versions) - 1
            v = st.session_state.artifact_versions[i]
            st.session_state.artifact_version_idx = i
            st.session_state.current_artifact = v["code"]
            st.session_state.current_files = v.get("files", {"index.html": v["code"]})
            st.session_state.current_thinking = v.get("thinking", "")
            st.session_state.artifact_lang = v["lang"]
            st.session_state.artifact_edit_mode = False
            st.session_state.selected_file = None

    elif _action == "artifact_next":
        if st.session_state.artifact_versions:
            i = (st.session_state.artifact_version_idx + 1) % len(
                st.session_state.artifact_versions
            )
            v = st.session_state.artifact_versions[i]
            st.session_state.artifact_version_idx = i
            st.session_state.current_artifact = v["code"]
            st.session_state.current_files = v.get("files", {"index.html": v["code"]})
            st.session_state.current_thinking = v.get("thinking", "")
            st.session_state.artifact_lang = v["lang"]
            st.session_state.artifact_edit_mode = False
            st.session_state.selected_file = None

    # ---- Modo edicao do artifact ----
    elif _action == "toggle_artifact_edit":
        st.session_state.artifact_edit_mode = not st.session_state.artifact_edit_mode

    elif _action == "cancel_artifact_edit":
        st.session_state.artifact_edit_mode = False

    # ---- Alternar visualizacao do preview ----
    elif _action == "view_preview":
        st.session_state.preview_view = "preview"

    elif _action == "view_code":
        st.session_state.preview_view = "code"


# ============================================================
# HELPERS DE TEXTO / PARSING
# ============================================================
_THINK_RE    = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_ARTIFACT_RE = re.compile(r"<artifact[^>]*>(.*?)</artifact>", re.DOTALL | re.IGNORECASE)
_HTML_BLOCK  = re.compile(r"```html\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_SVG_BLOCK   = re.compile(r"```svg\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_FILE_RE     = re.compile(r'<file\s+(?:name|path)=["\']([^"\']+)["\']\s*>(.*?)</file>', re.DOTALL | re.IGNORECASE)
_DANGLING_RE = re.compile(r"<(thinking|artifact)\b[^>]*>(?![^<]*</\1>)", re.IGNORECASE)


def _strip_dangling(text: str) -> str:
    return _DANGLING_RE.sub("", text)


def extract_thinking(text: str):
    blocks = _THINK_RE.findall(text)
    thinking = "\n\n".join(b.strip() for b in blocks)
    return _THINK_RE.sub("", text).strip(), thinking.strip()


def _detect_lang(code: str) -> str:
    if not code:
        return "html"
    lowered = code.lower()
    has_svg = "<svg" in lowered
    has_html = "<html" in lowered or "<!doctype" in lowered
    return "svg" if (has_svg and not has_html) else "html"


def extract_artifact(text: str):
    """Retorna (texto_visivel, codigo_bruto_do_artifact, lang)."""
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


def _parse_files(artifact_raw: str) -> dict:
    """Extrai multiplos arquivos de dentro do artifact (blocos <file>).
    Se nao houver nenhum, trata o conteudo inteiro como index.html."""
    files = {}
    for m in _FILE_RE.finditer(artifact_raw or ""):
        fname = m.group(1).strip()
        fcontent = m.group(2).strip()
        if fname:
            files[fname] = fcontent
    if not files:
        files["index.html"] = artifact_raw or ""
    return files


def _build_preview_html(files: dict) -> str:
    """Combina os arquivos (html/css/js) em um unico documento renderizavel."""
    html = files.get("index.html") or next(iter(files.values()), "")

    css_parts = [
        c for n, c in files.items()
        if n != "index.html" and n.lower().endswith(".css")
    ]
    js_parts = [
        c for n, c in files.items()
        if n != "index.html" and n.lower().endswith((".js", ".jsx"))
    ]

    if css_parts:
        style_tag = "<style>\n" + "\n".join(css_parts) + "\n</style>"
        html = (
            html.replace("</head>", style_tag + "\n</head>", 1)
            if "</head>" in html else style_tag + html
        )

    if js_parts:
        script_tag = "<script>\n" + "\n".join(js_parts) + "\n</script>"
        html = (
            html.replace("</body>", script_tag + "\n</body>", 1)
            if "</body>" in html else html + script_tag
        )

    return html


def _maybe_strip_emojis(text: str) -> str:
    """So remove emojis no modo padrao; se ha personalizacao definida
    pelo usuario (ex: 'sempre responda na zueira'), deixa o texto como
    o modelo escreveu, ja que emojis costumam fazer parte desse tom."""
    if (st.session_state.get("custom_instructions") or "").strip():
        return text or ""
    if not text:
        return text
    cleaned = re.sub(
        "["
        "\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF"
        "\U0001F700-\U0001F77F\U0000FE00-\U0000FE0F\U00002B00-\U00002BFF"
        "\U00002190-\U000021FF"
        "]+",
        "",
        text,
        flags=re.UNICODE,
    )
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +\n", "\n", cleaned)
    return cleaned


def parse_response(raw: str) -> dict:
    no_artifact, artifact_raw, lang = extract_artifact(raw)
    visible, thinking = extract_thinking(no_artifact)
    return {
        "text":         _maybe_strip_emojis(visible),
        "thinking":     thinking,
        "artifact_raw": artifact_raw,
        "lang":         lang,
    }


def _download_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"aether-artifact-{stamp}.html"


# ============================================================
# CONSTANTES DE LAYOUT
# ============================================================
PANEL_HEIGHT = 610
IFRAME_HEIGHT = 560


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
    :root, html, body { color-scheme: light !important; }
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

    /* ---------- FIX: texto do chat aparecendo branco ----------
       O streaming escreve via st.empty().markdown(...) e, dependendo do
       tema do navegador/SO, o Streamlit podia herdar cor de texto clara
       (branco) por baixo dos seletores mais especificos abaixo. Forcamos
       a cor em QUALQUER markdown renderizado no app, nao so no chat. */
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

    section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
        font-size: 12.5px !important;
        height: 32px !important;
        padding: 4px 10px !important;
        background: var(--panel) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
    }

    .sb-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 2px 14px 2px;
        margin-bottom: 6px;
        border-bottom: 1px solid var(--border-soft);
    }
    .sb-brand-mark {
        width: 32px; height: 32px;
        background: var(--accent);
        color: #ffffff;
        border-radius: var(--radius-md);
        display: flex; align-items: center; justify-content: center;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 17px; font-weight: 500;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(201,100,66,.22);
    }
    .sb-brand-info { display: flex; flex-direction: column; line-height: 1.15; }
    .sb-brand-name { font-size: 13.5px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
    .sb-brand-tag  { font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.02em; }

    .sb-section {
        font-size: 10px; font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.09em; text-transform: uppercase;
        padding: 14px 8px 6px 8px;
    }

    .sb-btn {
        display: flex !important;
        align-items: center; gap: 10px;
        padding: 8px 10px; margin: 1px 0;
        border-radius: var(--radius-sm);
        color: var(--text-dim) !important;
        font-size: 13px; font-weight: 500;
        text-decoration: none !important;
        transition: background-color 0.15s ease, color 0.15s ease;
        cursor: pointer; line-height: 1.2;
    }
    .sb-btn:hover { background: var(--panel); color: var(--text) !important; }
    .sb-btn svg { flex-shrink: 0; opacity: 0.75; }
    .sb-btn:hover svg { opacity: 1; }
    .sb-btn span { color: inherit; }
    .sb-btn.active { background: var(--panel); color: var(--accent) !important; }

    .sb-btn-primary {
        background: var(--accent);
        color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(201,100,66,.25);
        margin-bottom: 4px;
    }
    .sb-btn-primary:hover { background: var(--accent-hover); color: #ffffff !important; }
    .sb-btn-primary svg { opacity: 1; }

    .stApp p, .stApp span, .stApp li, .stApp label, .stApp div { color: var(--text); }

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
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 20px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        margin-bottom: 10px;
        box-shadow: var(--shadow-sm);
    }
    .app-header-left { display: flex; align-items: center; gap: 12px; }
    .app-brand-mark {
        width: 34px; height: 34px;
        background: var(--accent); color: #ffffff;
        border-radius: var(--radius-md);
        display: flex; align-items: center; justify-content: center;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 18px; font-weight: 500;
        box-shadow: 0 2px 6px rgba(201,100,66,.22);
        flex-shrink: 0;
    }
    .app-brand-info { line-height: 1.15; }
    .app-brand-name { font-size: 15px; font-weight: 600; color: var(--text); letter-spacing: -0.015em; }
    .app-brand-tag  { font-size: 11.5px; color: var(--text-mute); margin-top: 1px; }
    .app-status {
        display: inline-flex; align-items: center; gap: 7px;
        padding: 6px 12px;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        font-size: 12px; font-weight: 500;
        color: var(--text-dim);
    }
    .app-status-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #6ba944;
        box-shadow: 0 0 0 3px rgba(107,169,68,.15);
    }

    /* ---------- PANEL LABELS ---------- */
    .panel-label {
        display: flex; align-items: center; justify-content: space-between;
        padding: 2px 4px 8px 4px;
        font-size: 11px; font-weight: 600;
        color: var(--text-mute);
        letter-spacing: 0.1em; text-transform: uppercase;
    }
    .panel-label-title { display: flex; align-items: center; gap: 8px; }
    .panel-label-tools { display: flex; gap: 3px; align-items: center; }
    .panel-tool {
        width: 28px; height: 28px;
        display: flex; align-items: center; justify-content: center;
        color: var(--text-mute) !important;
        border-radius: 6px;
        text-decoration: none !important;
        cursor: pointer;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .panel-tool:hover { background: var(--panel); color: var(--accent) !important; }
    .panel-tool.active { background: var(--panel); color: var(--accent) !important; }

    .version-nav {
        display: inline-flex; align-items: center; gap: 2px;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-sm);
        padding: 2px;
        font-size: 11.5px;
        color: var(--text-dim);
    }
    .version-nav a {
        width: 22px; height: 22px;
        display: inline-flex; align-items: center; justify-content: center;
        color: var(--text-dim) !important;
        text-decoration: none !important;
        border-radius: 4px;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .version-nav a:hover { background: var(--card); color: var(--accent) !important; }
    .version-nav span {
        padding: 0 8px;
        font-variant-numeric: tabular-nums;
        font-size: 11.5px;
        color: var(--text-dim) !important;
    }

    /* ---------- DOWNLOAD / ACTION BUTTONS ---------- */
    [data-testid="stDownloadButton"] { margin: 0 !important; padding: 0 !important; }
    [data-testid="stDownloadButton"] > button {
        background: var(--card) !important;
        color: var(--text-dim) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        height: 28px !important; min-height: 28px !important;
        padding: 0 10px 0 8px !important;
        width: 100% !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important; justify-content: center !important;
        gap: 6px !important; cursor: pointer !important;
        transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.03) !important;
    }
    [data-testid="stDownloadButton"] > button:focus { box-shadow: none !important; outline: none !important; }
    [data-testid="stDownloadButton"] > button p {
        color: inherit !important; font-size: 12px !important;
        margin: 0 !important; white-space: nowrap !important;
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
        display: flex !important; flex-direction: row !important;
        align-items: flex-start !important; gap: 0 !important;
        animation: fadeUp 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }
    [data-testid="stChatMessage"] img {
        display: none !important; width: 0 !important; height: 0 !important;
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

    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) { margin-bottom: 16px !important; }
    [data-testid="stChatMessage"]:has(img[src*="aiavatar"]) [data-testid="stChatMessageContent"]::before {
        content: "AETHER";
        display: block;
        font-size: 10.5px; font-weight: 700;
        color: var(--text-mute);
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li {
        color: var(--text) !important;
        font-size: 14.5px; line-height: 1.65;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(3px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ---- Acoes de mensagem (editar / regenerar) ---- */
    .msg-actions {
        display: flex; gap: 12px; align-items: center;
        margin-top: 6px; opacity: 0;
        transition: opacity 0.15s ease;
    }
    [data-testid="stChatMessage"]:hover .msg-actions { opacity: 1; }
    .msg-action {
        font-size: 11.5px;
        color: var(--text-mute) !important;
        text-decoration: none !important;
        cursor: pointer;
        font-weight: 500;
        display: inline-flex; align-items: center; gap: 4px;
        transition: color 0.15s ease;
    }
    .msg-action:hover { color: var(--accent) !important; }

    .artifact-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 10px;
        margin-top: 10px;
        background: rgba(201,100,66,.08);
        border: 1px solid rgba(201,100,66,.22);
        border-radius: 999px;
        font-size: 11px; font-weight: 600;
        color: var(--accent) !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .artifact-badge::before {
        content: "";
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--accent);
    }

    /* ---- Form inline de edicao ---- */
    [data-testid="stForm"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 10px 12px !important;
    }
    [data-testid="stChatMessage"] [data-testid="stForm"] {
        border: 1px solid var(--accent) !important;
        padding: 8px 10px !important;
        margin-top: 6px !important;
    }
    [data-testid="stTextArea"] textarea {
        font-size: 14px !important;
        line-height: 1.55 !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 8px 10px !important;
        background: var(--bg) !important;
    }

    [data-testid="stChatMessage"] [data-testid="stCode"],
    [data-testid="stChatMessage"] pre,
    .stCodeBlock pre {
        background: var(--bg-code) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stChatMessage"] pre code,
    [data-testid="stChatMessage"] [data-testid="stCode"] code,
    .stCodeBlock code {
        background: transparent !important;
        color: var(--text) !important;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace !important;
        font-size: 12.5px !important; line-height: 1.6 !important;
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

    [data-testid="stExpander"] {
        border: 1px solid var(--border-soft) !important;
        background: var(--panel) !important;
        border-radius: var(--radius-sm) !important;
        margin: 0 0 8px 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] {
        border: none !important; background: transparent !important;
        margin: 0 0 8px 0 !important; padding: 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] details {
        border: none !important; background: transparent !important; padding: 0 !important;
    }
    [data-testid="stExpander"] summary {
        padding: 6px 10px !important;
        font-size: 12px !important;
        color: var(--text-dim) !important;
        font-weight: 500 !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary {
        padding: 2px 0 !important;
        color: var(--text-mute) !important;
        list-style: none !important;
        opacity: 0.8;
        transition: opacity 0.15s ease, color 0.15s ease;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary:hover {
        opacity: 1; color: var(--accent) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary p {
        font-size: 12px !important; color: inherit !important; display: inline !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary svg {
        width: 10px !important; height: 10px !important;
        opacity: 0.6; margin-right: 6px;
    }
    [data-testid="stExpanderDetails"] {
        padding: 6px 10px 10px 10px !important;
        background: transparent !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] {
        border-left: 2px solid var(--border-soft) !important;
        padding: 6px 0 6px 14px !important;
        margin: 6px 0 10px 0 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stExpanderDetails"] p {
        font-size: 12.5px !important;
        color: var(--text-dim) !important;
        line-height: 1.65; font-style: italic; opacity: 0.9;
    }

    /* ---------- FORMS (config / editar / salvar projeto) ----------
       Estilo padrao para botoes de submit de formularios que NAO sao o
       composer (o composer e diferenciado abaixo via :has() no proprio
       input, ja que um <div> criado com st.markdown nao consegue
       "envolver" outros elementos do Streamlit no DOM). */
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

    /* ---------- COMPOSER (identificado pelo placeholder do input) ---------- */
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) {
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
        margin-top: 4px;
        padding: 6px 10px !important;
    }
    [data-testid="stForm"] > div > [data-testid="stVerticalBlock"] { gap: 0 !important; }
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important; gap: 6px !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stTextInput"] > div {
        border: none !important; background: transparent !important; box-shadow: none !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stTextInput"] input {
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
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stTextInput"] input::placeholder {
        color: var(--text-mute) !important;
        -webkit-text-fill-color: var(--text-mute) !important;
        opacity: 1 !important;
    }

    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stPopover"] > button {
        width: 40px !important; height: 40px !important; min-width: 40px !important;
        padding: 0 !important; font-size: 0 !important; color: transparent !important;
        background-color: transparent !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23999999' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        transition: border-color 0.15s ease, background-color 0.15s ease !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stPopover"] > button:hover {
        background-color: var(--panel) !important;
        border-color: var(--accent) !important;
    }

    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stFormSubmitButton"] button {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        width: 44px !important; height: 44px !important; min-width: 44px !important;
        padding: 0 !important; font-size: 0 !important;
        box-shadow: 0 2px 6px rgba(201,100,66,.28) !important;
        transition: background-color 0.15s ease, transform 0.15s ease !important;
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 2L11 13M22 2l-7 20-4-9-9-4z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
    }
    [data-testid="stForm"]:has(input[placeholder="Envie uma mensagem para o Aether Engine..."]) [data-testid="stFormSubmitButton"] button:hover {
        background-color: var(--accent-hover) !important;
        transform: translateY(-1px);
    }

    .composer-mic {
        width: 40px !important; height: 40px !important;
        display: inline-flex !important;
        align-items: center !important; justify-content: center !important;
        color: var(--text-mute) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: var(--radius-sm) !important;
        text-decoration: none !important; background: transparent;
        transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
    }
    .composer-mic:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--panel);
        text-decoration: none !important;
    }

    .attach-chip {
        display: inline-flex; align-items: center; gap: 8px;
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
        text-decoration: none; font-weight: 600;
        margin-left: 4px; transition: color 0.15s ease;
    }
    .attach-chip a:hover { color: var(--accent) !important; }

    /* ---------- STOP BUTTON ---------- */
    .stop-wrap {
        display: flex; justify-content: center;
        margin: 4px 0 8px 0;
    }
    .stop-wrap a {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 12px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 999px;
        font-size: 12px; font-weight: 500;
        color: var(--text-dim) !important;
        text-decoration: none !important;
        transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease;
    }
    .stop-wrap a:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(201,100,66,.04);
    }

    /* ---------- PREVIEW ---------- */
    .preview-empty {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center;
        padding: 40px 24px;
        min-height: 480px;
    }
    .preview-empty-icon {
        width: 78px; height: 78px;
        display: flex; align-items: center; justify-content: center;
        background: var(--panel);
        border: 1px solid var(--border-soft);
        border-radius: 50%;
        color: var(--text-mute);
        margin-bottom: 22px;
    }
    .preview-empty-title {
        font-size: 15.5px; font-weight: 600;
        color: var(--text) !important;
        margin-bottom: 8px; letter-spacing: -0.01em;
    }
    .preview-empty-text {
        font-size: 13px;
        color: var(--text-mute) !important;
        line-height: 1.6; max-width: 320px; margin-bottom: 20px;
    }
    .preview-empty-btn {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 8px 16px;
        background: var(--card);
        color: var(--text) !important;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-size: 13px; font-weight: 500;
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
        width: 2px; height: 1.05em;
        background: var(--accent);
        vertical-align: text-bottom;
        margin-left: 2px;
        animation: blink 1s step-start infinite;
        opacity: 0.7;
    }
    @keyframes blink { 50% { opacity: 0; } }

    /* file tree do modo "codigo" */
    .file-row {
        display: flex; align-items: center; gap: 8px;
        padding: 7px 10px; border-radius: var(--radius-sm);
        font-size: 12.5px; color: var(--text-dim) !important;
        cursor: pointer; margin-bottom: 2px;
    }
    .file-row.active { background: var(--panel); color: var(--accent) !important; font-weight: 600; }

    /* ---------- LISTAS (historico / projetos) ---------- */
    .hist-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 6px; border-bottom: 1px solid var(--border-soft);
        gap: 8px;
    }
    .hist-row-main { flex: 1 1 auto; min-width: 0; text-decoration: none !important; }
    .hist-title {
        font-size: 13.5px; font-weight: 500; color: var(--text) !important;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .hist-meta { font-size: 11px; color: var(--text-mute) !important; margin-top: 2px; }
    .hist-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
    .hist-action {
        color: var(--text-mute) !important; text-decoration: none !important;
        display: inline-flex; align-items: center; cursor: pointer;
        transition: color 0.15s ease;
    }
    .hist-action:hover { color: var(--accent) !important; }
    .hist-action.pinned { color: var(--accent) !important; }
    .panel-empty {
        padding: 30px 10px; text-align: center;
        color: var(--text-mute); font-size: 13px; line-height: 1.6;
    }
    .panel-back {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 12.5px; font-weight: 500;
        color: var(--text-dim) !important;
        text-decoration: none !important;
        margin-bottom: 8px;
        transition: color 0.15s ease;
    }
    .panel-back:hover { color: var(--accent) !important; }
    .settings-hint {
        font-size: 12px; color: var(--text-mute) !important;
        line-height: 1.6; margin-bottom: 10px;
    }
    .settings-section {
        font-size: 11px; font-weight: 600; color: var(--text-mute);
        letter-spacing: 0.08em; text-transform: uppercase;
        margin: 16px 0 8px 0;
    }

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
        box-shadow: none !important; cursor: pointer !important;
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
    ::-webkit-scrollbar-thumb { background: #dedbd3; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #c9c6be; }

    /* ---------- MENU MOBILE ---------- */
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
        .block-container { padding: 0.4rem 0.75rem 0.4rem 0.75rem !important; }
        .app-header { padding: 8px 12px 8px 52px !important; }
        .app-brand-name { font-size: 14px; }
        .app-status { padding: 5px 10px; font-size: 11px; }
        .preview-empty { min-height: 340px; padding: 24px 16px; }
        .preview-empty-icon { width: 64px; height: 64px; margin-bottom: 16px; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# ATALHO: ESC cancela edicao
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
            <div class="sb-brand-tag">Workspace</div>
        </div>
    </div>

    <a class="sb-btn sb-btn-primary" href="?a=new" target="_self">
        {ICON_PLUS}<span>Novo projeto</span>
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
    st.session_state.search_query = st.text_input(
        "Buscar na conversa",
        value=st.session_state.search_query,
        placeholder="Filtrar mensagens...",
        label_visibility="collapsed",
        key="sidebar_search",
    )


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
# PAINEIS: HISTORICO / PROJETOS / CONFIGURACOES
# (renderizados dentro da coluna do chat, no lugar da conversa)
# ============================================================
def _hist_row_html(c: dict, show_pin: bool = True) -> str:
    pin_cls = "hist-action pinned" if c["pinned"] else "hist-action"
    pin_title = "Remover dos projetos" if c["pinned"] else "Salvar como projeto"
    pin_html = (
        f'<a class="{pin_cls}" href="?a=toggle_pin_conv&i={c["id"]}" '
        f'target="_self" title="{pin_title}">{ICON_STAR}</a>'
        if show_pin else ""
    )
    return f"""
    <div class="hist-row">
        <a class="hist-row-main" href="?a=load_conv&i={c['id']}" target="_self">
            <div class="hist-title">{c['title']}</div>
            <div class="hist-meta">{c['ts']} · {len(c['messages'])} mensagens</div>
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
    box = st.container(height=PANEL_HEIGHT)
    with box:
        st.markdown(
            '<div style="font-size:14px;font-weight:600;margin-bottom:4px;">'
            'Personalizacao</div>'
            '<div class="settings-hint">'
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
                placeholder="Ex: sempre responda na zueira, com girias brasileiras, "
                            "sem formalidade, pode usar emoji...",
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
    box = st.container(height=PANEL_HEIGHT)
    with box:
        if not st.session_state.conversations:
            st.markdown(
                '<div class="panel-empty">Nenhuma conversa salva ainda.<br>'
                'Conversas anteriores aparecem aqui quando voce clica em '
                '"Novo projeto".</div>',
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
    box = st.container(height=PANEL_HEIGHT)
    with box:
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
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        pinned = [c for c in st.session_state.conversations if c["pinned"]]
        if not pinned:
            st.markdown(
                '<div class="panel-empty">Nenhum projeto salvo ainda.<br>'
                'Salve a conversa atual acima, ou marque uma conversa do '
                'historico com a estrela.</div>',
                unsafe_allow_html=True,
            )
        else:
            for c in pinned:
                st.markdown(_hist_row_html(c), unsafe_allow_html=True)


# ============================================================
# LAYOUT
# ============================================================
col_chat, col_preview = st.columns([1, 1.15], gap="medium")


# ------------------------------------------------------------
# CHAT
# ------------------------------------------------------------
_do_rerun = False
_panel_active = (
    st.session_state.show_settings
    or st.session_state.show_history
    or st.session_state.show_projects
)

with col_chat:

    _panel_title = (
        "Configuracoes" if st.session_state.show_settings
        else "Historico" if st.session_state.show_history
        else "Projetos" if st.session_state.show_projects
        else "Conversa"
    )
    st.markdown(
        f'<div class="panel-label"><span class="panel-label-title">{_panel_title}</span></div>',
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
        salvar_historico_no_disco()  # Salva a mensagem do usuário imediatamente


    if st.session_state.show_settings:
        _render_settings_panel()
    elif st.session_state.show_history:
        _render_history_panel()
    elif st.session_state.show_projects:
        _render_projects_panel()
    else:
        _query = (st.session_state.search_query or "").strip().lower()

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
                            with st.expander("Processando raciocinio"):
                                st.markdown(msg["thinking"])
                        if msg.get("content"):
                            st.markdown(msg["content"])
                        if msg.get("has_artifact"):
                            _fnames = msg.get("artifact_files") or []
                            _badge_extra = (
                                " · " + ", ".join(_fnames) if len(_fnames) > 1 else ""
                            )
                            st.markdown(
                                '<span class="artifact-badge">Artifact '
                                f'{(msg.get("artifact_lang") or "html").upper()}'
                                f'{_badge_extra}</span>',
                                unsafe_allow_html=True,
                            )
                        is_last = (i == len(st.session_state.messages) - 1)
                        if is_last:
                            st.markdown(
                                f'<div class="msg-actions">'
                                f'<a class="msg-action" href="?a=regen" target="_self">'
                                f'{ICON_REFRESH}<span>regenerar</span></a>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

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

                    thinking_slot = st.expander("Processando raciocinio", expanded=False)
                    with thinking_slot:
                        thinking_body = st.empty()

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

                                partial_visible, partial_think = extract_thinking(raw_buffer)
                                partial_visible, _, _ = extract_artifact(partial_visible)
                                partial_visible = _strip_dangling(partial_visible)
                                partial_visible = _maybe_strip_emojis(partial_visible)

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

                        stop_holder.empty()

                        parsed = parse_response(raw_buffer)
                        final_thinking = "\n\n".join(
                            filter(None, [reasoning_accum, parsed["thinking"]])
                        )

                        if final_thinking:
                            thinking_body.markdown(final_thinking)
                        else:
                            thinking_body.markdown("_Sem raciocinio exposto._")

                        text_body.markdown(parsed["text"] or "_Sem resposta._")

                        has_artifact = bool(parsed["artifact_raw"])
                        art_lang = parsed["lang"]
                        files_dict = {}
                        preview_html = None

                        if has_artifact:
                            files_dict = _parse_files(parsed["artifact_raw"])
                            preview_html = _build_preview_html(files_dict)

                            st.session_state.artifact_versions.append({
                                "code":     preview_html,
                                "files":    files_dict,
                                "lang":     art_lang,
                                "ts":       datetime.now().strftime("%H:%M:%S"),
                                "prompt":   (st.session_state.messages[-1]["content"] or "")[:60],
                                "thinking": final_thinking,
                            })
                            st.session_state.artifact_version_idx = (
                                len(st.session_state.artifact_versions) - 1
                            )
                            st.session_state.current_artifact = preview_html
                            st.session_state.current_files = files_dict
                            st.session_state.current_thinking = final_thinking
                            st.session_state.artifact_lang = art_lang
                            st.session_state.preview_view = "preview"
                            st.session_state.selected_file = None

                            _fnames = list(files_dict.keys())
                            _badge_extra = (
                                " · " + ", ".join(_fnames) if len(_fnames) > 1 else ""
                            )
                            st.markdown(
                                '<span class="artifact-badge">Artifact '
                                f'{(art_lang or "html").upper()}{_badge_extra}</span>',
                                unsafe_allow_html=True,
                            )

                        st.session_state.messages.append({
                            "role":            "assistant",
                            "content":         parsed["text"],
                            "thinking":        final_thinking,
                            "has_artifact":    has_artifact,
                            "artifact_lang":   art_lang if has_artifact else None,
                            "artifact_files":  list(files_dict.keys()) if has_artifact else [],
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

    has_art = bool(st.session_state.current_artifact)
    total_v = len(st.session_state.artifact_versions)
    cur_v   = st.session_state.artifact_version_idx + 1 if total_v else 0
    files_dict = st.session_state.current_files or {}
    is_multi_file = len(files_dict) > 1

    hdr_l, hdr_toggle, hdr_v, hdr_t, hdr_e, hdr_r = st.columns(
        [2.2, 0.55, 1.35, 0.55, 0.55, 1.6],
        gap="small",
        vertical_alignment="center",
    )

    with hdr_l:
        st.markdown(
            '<div class="panel-label" style="padding:0;margin:0;">'
            '<span class="panel-label-title">Preview</span></div>',
            unsafe_allow_html=True,
        )

    with hdr_toggle:
        if has_art:
            if st.session_state.preview_view == "preview":
                st.markdown(
                    f'<a class="panel-tool" href="?a=view_code" target="_self" '
                    f'title="Ver codigo">{ICON_CODE}</a>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<a class="panel-tool" href="?a=view_preview" target="_self" '
                    f'title="Ver preview">{ICON_EYE}</a>',
                    unsafe_allow_html=True,
                )

    with hdr_v:
        if has_art and total_v > 0:
            st.markdown(
                f'<div class="version-nav">'
                f'<a href="?a=artifact_prev" target="_self" title="Versao anterior">{ICON_BACK}</a>'
                f'<span>{cur_v}/{total_v}</span>'
                f'<a href="?a=artifact_next" target="_self" title="Proxima versao">{ICON_NEXT}</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with hdr_t:
        st.markdown(
            f'<a class="panel-tool" href="?a=refresh" target="_self" '
            f'title="Atualizar">{ICON_REFRESH}</a>',
            unsafe_allow_html=True,
        )

    with hdr_e:
        if has_art and st.session_state.preview_view == "preview":
            tool_href = (
                "?a=cancel_artifact_edit"
                if st.session_state.artifact_edit_mode
                else "?a=toggle_artifact_edit"
            )
            tool_title = (
                "Fechar edicao" if st.session_state.artifact_edit_mode
                else "Editar codigo"
            )
            st.markdown(
                f'<a class="panel-tool" href="{tool_href}" target="_self" '
                f'title="{tool_title}">{ICON_EDIT}</a>',
                unsafe_allow_html=True,
            )

    with hdr_r:
        if has_art:
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
        if not has_art:
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

        else:
            # ---- Painel "o que a IA esta fazendo" (estilo Arena) ----
            if st.session_state.current_thinking or is_multi_file:
                with st.expander("Raciocinio da IA", expanded=False):
                    if st.session_state.current_thinking:
                        st.markdown(st.session_state.current_thinking)
                    if files_dict:
                        _names = ", ".join(f"`{n}`" for n in files_dict.keys())
                        st.markdown(f"**Arquivos gerados:** {_names}")

            if st.session_state.preview_view == "code":
                # ---- Modo Codigo: arvore de arquivos + visualizador ----
                file_names = list(files_dict.keys())
                if (
                    st.session_state.selected_file not in file_names
                    and file_names
                ):
                    st.session_state.selected_file = file_names[0]

                f_col1, f_col2 = st.columns([1, 2.4], gap="small")
                with f_col1:
                    st.markdown(
                        '<div style="font-size:11px;font-weight:600;'
                        'color:var(--text-mute);letter-spacing:.08em;'
                        'text-transform:uppercase;margin-bottom:8px;">'
                        'Arquivos</div>',
                        unsafe_allow_html=True,
                    )
                    for fname in file_names:
                        if st.button(
                            fname,
                            key=f"filebtn_{fname}_{st.session_state.artifact_version_idx}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_file = fname
                            st.rerun()

                with f_col2:
                    if st.session_state.selected_file:
                        _ext = st.session_state.selected_file.rsplit(".", 1)[-1].lower()
                        _lang_map = {
                            "html": "html", "css": "css", "js": "javascript",
                            "jsx": "jsx", "json": "json", "py": "python",
                            "md": "markdown",
                        }
                        st.code(
                            files_dict[st.session_state.selected_file],
                            language=_lang_map.get(_ext, "text"),
                        )

            elif st.session_state.artifact_edit_mode:
                # Modo edicao: substitui o iframe por um textarea.
                # A key inclui o indice da versao para nao "prender" o
                # textarea no conteudo de uma versao antiga.
                _edit_key = f"artifact_edit_area_{st.session_state.artifact_version_idx}"
                with st.form("artifact_edit_form", clear_on_submit=False):
                    st.markdown(
                        '<div style="font-size:11px;font-weight:600;'
                        'color:#c96442;letter-spacing:.08em;'
                        'text-transform:uppercase;margin-bottom:6px;">'
                        'Editando artifact (HTML combinado)'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    edited = st.text_area(
                        "Codigo",
                        value=st.session_state.current_artifact,
                        height=IFRAME_HEIGHT - 110,
                        label_visibility="collapsed",
                        key=_edit_key,
                    )
                    ec1, ec2 = st.columns([1.4, 1])
                    with ec1:
                        apply_edit = st.form_submit_button(
                            "Aplicar", use_container_width=True,
                        )
                    with ec2:
                        cancel_edit = st.form_submit_button(
                            "Cancelar", use_container_width=True,
                        )
                    if apply_edit:
                        st.session_state.current_artifact = edited
                        st.session_state.current_files = {"index.html": edited}
                        if (
                            st.session_state.artifact_versions
                            and 0 <= st.session_state.artifact_version_idx
                            < len(st.session_state.artifact_versions)
                        ):
                            _v = st.session_state.artifact_versions[
                                st.session_state.artifact_version_idx
                            ]
                            _v["code"] = edited
                            _v["files"] = {"index.html": edited}
                        st.session_state.artifact_edit_mode = False
                        st.rerun()
                    if cancel_edit:
                        st.session_state.artifact_edit_mode = False
                        st.rerun()

            else:
                # Comentario invisivel para forcar o navegador a remontar
                # o iframe de verdade quando "Atualizar" e clicado, ou
                # quando a versao muda.
                _cache_bust = (
                    f"\n<!-- aether-preview-refresh:{st.session_state.refresh_counter}"
                    f"-v{st.session_state.artifact_version_idx} -->"
                )
                components.html(
                    st.session_state.current_artifact + _cache_bust,
                    height=IFRAME_HEIGHT,
                    scrolling=True,
                )


# ============================================================
# RERUN
# ============================================================
if _do_rerun:
    st.rerun()
