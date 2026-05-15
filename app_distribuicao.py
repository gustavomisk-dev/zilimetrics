"""
Streamlit — Distribuição de contratos taxa 4,98%.
Executar: streamlit run distribuicao_nova_taxa/app_distribuicao.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import io
import json
import bcrypt
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent))
from dados import ANALISES, get_grupo, load_data, distribuicao

HERE = Path(__file__).parent

# ── Autenticação ──────────────────────────────────────────────────────────────

_login_attempts: dict = {}


def load_users() -> dict:
    if "users" in st.secrets:
        return {u: dict(data) for u, data in st.secrets["users"].items()}
    path = HERE / "users.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def login_page() -> None:
    st.markdown(f"""
        <div style="text-align:center; margin-top:5rem; margin-bottom:2.5rem;">
            <h1 style="color:{GOLD}; font-size:2.8rem; font-weight:700;
                       letter-spacing:1px; margin-bottom:0.3rem;">
                ZiliMetrics
            </h1>
            <p style="color:{MUTED}; font-size:0.95rem; margin:0;">
                Análise de Dados
            </p>
        </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login_form"):
            username  = st.text_input("Usuário")
            password  = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        attempt = _login_attempts.get(username, {"count": 0, "blocked_until": None})
        blocked_until = attempt["blocked_until"]

        if blocked_until and datetime.now() < blocked_until:
            remaining = int((blocked_until - datetime.now()).total_seconds() / 60)
            with col:
                st.error(f"Usuário bloqueado. Tente novamente em {remaining} minuto(s).")
            return

        users = load_users()
        user  = users.get(username)
        try:
            pw_ok = user is not None and bcrypt.checkpw(
                password.encode(), user["password"].encode()
            )
        except Exception:
            pw_ok = False

        if pw_ok:
            _login_attempts.pop(username, None)
            st.session_state.update({
                "logged_in":      True,
                "display_name":   user.get("display_name", username),
                "is_admin":       user.get("is_admin", False),
                "expand_sidebar": True,
            })
            st.rerun()
        else:
            attempt["count"] += 1
            if attempt["count"] >= 3:
                attempt["blocked_until"] = datetime.now() + timedelta(hours=1)
            _login_attempts[username] = attempt
            with col:
                if attempt["count"] >= 3:
                    st.error("Usuário bloqueado por 1 hora após tentativas inválidas.")
                else:
                    st.error("Usuário ou senha incorretos.")


# ── Config ────────────────────────────────────────────────────────────────────

GOLD      = "#F0B429"
DARK_CARD = "#1A1A1A"
BORDER    = "#262626"
MUTED     = "#6B7280"

CSS = f"""
<style>
/* ── chrome do Streamlit ─────────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stToolbarActions"] {{ visibility: hidden; }}
[data-testid="stBaseButton-header"] {{ visibility: hidden; }}
[data-testid="InputInstructions"] {{ display: none !important; }}
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {{ display: none !important; }}

/* ── fundo geral ─────────────────────────────────────────────── */
.stApp {{ background-color: #0F0F0F; }}

/* ── sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {{
    width: 260px !important;
    min-width: 260px !important;
    max-width: 260px !important;
    background-color: #111111;
    border-right: 1px solid {BORDER};
    padding-top: 1.5rem;
}}

/* ── botão primário ──────────────────────────────────────────── */
.stButton > button {{
    background-color: {GOLD} !important;
    color: #0F0F0F !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: background-color 0.15s;
}}
.stButton > button:hover {{
    background-color: #D4980F !important;
    color: #0F0F0F !important;
}}

/* ── botão de download ───────────────────────────────────────── */
.stDownloadButton > button {{
    background-color: transparent !important;
    color: {GOLD} !important;
    border: 1px solid {GOLD} !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}}
.stDownloadButton > button:hover {{
    background-color: rgba(240,180,41,0.08) !important;
}}

/* ── inputs de texto ─────────────────────────────────────────── */
div[data-baseweb="input"] > div {{
    background-color: {DARK_CARD} !important;
    border-color: #333333 !important;
    border-radius: 6px !important;
}}
div[data-baseweb="input"] > div:focus-within {{
    border-color: {GOLD} !important;
    box-shadow: none !important;
}}
div[data-baseweb="input"] input,
div[data-baseweb="input"] input[type="password"] {{
    height: 2rem !important;
    line-height: 2rem !important;
}}

/* ── selectbox ───────────────────────────────────────────────── */
div[data-baseweb="select"] > div {{
    background-color: {DARK_CARD} !important;
    border-color: #333333 !important;
    border-radius: 6px !important;
}}
div[data-baseweb="select"] > div:focus-within {{
    border-color: {GOLD} !important;
    box-shadow: none !important;
}}

/* ── dataframe ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    overflow: hidden;
}}

/* ── menu lateral (radio sem bolinhas) ───────────────────────── */
[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
    gap: 2px !important;
}}
[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label > div:first-child {{
    display: none !important;
}}
[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label {{
    padding: 0.45rem 0.75rem !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: background-color 0.15s !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:hover {{
    background-color: rgba(255,255,255,0.05) !important;
}}
[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) {{
    background-color: rgba(240,180,41,0.12) !important;
    color: {GOLD} !important;
    font-weight: 600 !important;
}}

/* ── divisor ─────────────────────────────────────────────────── */
hr {{ border-color: {BORDER} !important; }}
</style>
"""

st.set_page_config(
    page_title="ZiliMetrics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)

@st.cache_resource
def _get_shared():
    return {"csv_bytes": None}

_SHARED = _get_shared()

if not st.session_state.get("logged_in"):
    login_page()
    st.stop()

CORES = {
    "Todos":     "#1f77b4",
    "Suspenso":  "#d62728",
    "Aprovado":  "#2ca02c",
}

# ── Lookups CBO / CNAE ───────────────────────────────────────────────────────

@st.cache_data(show_spinner="Carregando nomes CNAE…")
def load_cnae_names() -> dict:
    try:
        r = requests.get(
            "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses",
            timeout=15,
        )
        r.raise_for_status()
        result = {}
        for item in r.json():
            raw = str(item["id"])
            bare = raw.replace("-", "")
            result[bare] = item["descricao"]
            result[raw] = item["descricao"]
        return result
    except Exception:
        return {}


@st.cache_data(show_spinner="Carregando nomes CBO…")
def load_cbo_names() -> dict:
    urls = [
        "https://raw.githubusercontent.com/datasets-br/cbo/master/data/lista.csv",
        "https://cdn.jsdelivr.net/gh/datasets-br/cbo@master/data/lista.csv",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            priority = {"Ocupacao": 0, "Sinônimo": 1, "Família": 2}
            df = pd.read_csv(io.StringIO(r.text), dtype=str)
            df["_p"] = df["tipo"].map(priority).fillna(9)
            df = df.sort_values("_p")
            result: dict = {}
            family: dict = {}
            for _, row in df.iterrows():
                code = str(row["codigo"])
                name = str(row["termo"])
                bare = code.replace("-", "")
                if bare not in result:
                    result[bare] = name
                if code not in result:
                    result[code] = name
                if row["tipo"] == "Família" and len(bare) == 4:
                    family[bare] = name
            result["_family"] = family
            return result
        except Exception:
            continue
    return {}


def _show_lookup_table(codes: list, lookup_dict: dict) -> None:
    family = lookup_dict.get("_family", {})

    def _lookup(c: str) -> str:
        bare = c.replace("-", "")
        name = lookup_dict.get(bare) or lookup_dict.get(c)
        if not name:
            name = family.get(bare[:4], "—")
        return name or "—"

    rows = [{"Código": c, "Nome": _lookup(c)} for c in codes if c != "Não Informado"]
    if rows:
        st.dataframe(pd.DataFrame(rows).set_index("Código"), use_container_width=True)


# ── Carrega dados ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Carregando dados…")
def _load(file_bytes: bytes):
    import io
    return load_data(io.BytesIO(file_bytes))


is_admin = st.session_state.get("is_admin", False)

# ── Sidebar — sempre renderizada ──────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
        <div style="padding:0 0.5rem 0.75rem 0.5rem;">
            <span style="font-size:1.35rem; font-weight:700; color:{GOLD}; letter-spacing:0.5px;">
                ZiliMetrics
            </span><br>
            <span style="font-size:0.78rem; color:{MUTED};">ZiliCred</span>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown(
        f"<p style='font-size:0.85rem; color:{MUTED}; margin-bottom:0.5rem;'>"
        f"{st.session_state.get('display_name', '')}</p>",
        unsafe_allow_html=True,
    )
    if st.button("Sair", use_container_width=True):
        for key in ["logged_in", "display_name", "is_admin"]:
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()


# ── JavaScript sidebar ────────────────────────────────────────────────────────

components.html("""
    <script>
    (function() {
        function removeResizeHandles() {
            var doc = window.parent.document;
            doc.querySelectorAll('*').forEach(function(el) {
                var cursor = window.parent.getComputedStyle(el).cursor;
                if (cursor === 'col-resize' || cursor === 'ew-resize') {
                    el.style.pointerEvents = 'none';
                    el.style.display = 'none';
                }
            });
        }
        setTimeout(removeResizeHandles, 300);
        setTimeout(removeResizeHandles, 1000);
    })();
    </script>
""", height=0, scrolling=False)

if st.session_state.pop("expand_sidebar", False):
    components.html("""
        <script>
        setTimeout(function() {
            try {
                var btn = window.parent.document.querySelector(
                    '[data-testid="collapsedControl"] button, [data-testid="collapsedControl"]'
                );
                if (btn) btn.click();
            } catch(e) {}
        }, 200);
        </script>
    """, height=0, scrolling=False)

# ── Upload na sidebar (admin) ─────────────────────────────────────────────────

if is_admin:
    with st.sidebar:
        st.divider()
        st.markdown(
            f"<p style='font-weight:600; color:{GOLD}; margin-bottom:0.4rem;'>Upload de Relatório</p>",
            unsafe_allow_html=True,
        )
        st.session_state.setdefault("_up_n", 0)
        uploaded = st.file_uploader(
            "Relatório CSV",
            type="csv",
            accept_multiple_files=False,
            key=f"_uploader_{st.session_state['_up_n']}",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            if st.button("Salvar", use_container_width=True):
                _SHARED["csv_bytes"] = uploaded.read()
                st.cache_data.clear()
                st.session_state["_up_n"] += 1
                st.rerun()

# ── Verifica dados ────────────────────────────────────────────────────────────

if _SHARED["csv_bytes"] is None:
    if not is_admin:
        st.info("⏳ Nenhum dado disponível no momento. Aguarde o administrador carregar o relatório.")
    st.stop()

df = _load(_SHARED["csv_bytes"])

# ── Filtros na sidebar (só após ter dados) ────────────────────────────────────

with st.sidebar:
    st.markdown(f"<p style='font-weight:600; color:{GOLD};'>Filtros</p>", unsafe_allow_html=True)
    grupo = st.radio(
        "Grupo",
        ["Todos", "Suspenso", "Aprovado"],
        index=0,
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"Total na base: {len(df):,} contratos")
    st.caption(f"Suspensos: {(df['Status do Processo']=='Suspenso').sum():,}")
    st.caption(f"Aprovados: {(df['Status do Processo']=='Aprovado').sum():,}")

df_view = get_grupo(df, grupo)
cor = CORES[grupo]

# ── Cabeçalho ─────────────────────────────────────────────────────────────────

st.title(f"📊 Distribuição Taxa 4,98% — {grupo}")

n_contratos   = len(df_view)
n_aprov       = (df_view["Status do Processo"] == "Aprovado").sum()
n_susp        = (df_view["Status do Processo"] == "Suspenso").sum()
valor_total   = df_view["_valor_contrat"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Contratos",    f"{n_contratos:,}")
c2.metric("Suspensos",    f"{n_susp:,}")
c3.metric("Aprovados",    f"{n_aprov:,}")
c4.metric("Valor Total",  f"R$ {valor_total:,.2f}" if valor_total > 0 else "—")

st.divider()

# ── Função de renderização ────────────────────────────────────────────────────

def render_analise(analise: dict, grupo: str) -> None:
    nome = analise["nome"]
    aid  = analise["id"]
    obs  = analise.get("obs", "")

    st.subheader(nome)
    if obs:
        st.caption(f"ℹ️ {obs}")

    tab_ct, tab_val = st.tabs(["Por número de contratos", "Por valor de contratação (R$)"])

    with tab_ct:
        dist = distribuicao(df_view, analise, "contratos")
        _render_chart(dist, "Contratos", cor, analise, key=f"{grupo}_{aid}_ct")

    with tab_val:
        sem_valor = df_view["_valor_contrat"].isna().all()
        if sem_valor:
            st.info("Dados de valor de contratação não disponíveis para este grupo "
                    "(apenas Aprovados possuem Valor de Contratação preenchido).")
        else:
            dist = distribuicao(df_view, analise, "valor")
            _render_chart(dist, "Valor (R$)", cor, analise, fmt_moeda=True, key=f"{grupo}_{aid}_val")


def _render_chart(
    dist: pd.DataFrame,
    x_label: str,
    cor: str,
    analise: dict,
    fmt_moeda: bool = False,
    key: str = "",
) -> None:
    val_col = "valor_dim"
    total = dist[val_col].sum()
    if total == 0:
        st.info("Nenhum dado disponível para este grupo/dimensão.")
        return

    def _fmt(v):
        return f"R$ {v:,.2f}" if fmt_moeda else f"{int(v):,}"

    dist = dist.copy()
    dist["label"] = dist.apply(
        lambda r: f"{_fmt(r[val_col])}  ({r['pct']:.1f}%)", axis=1
    )

    if analise["tipo"] == "top20":
        dist = dist[dist[val_col] > 0]

    cats_order = dist["categoria"].tolist()[::-1]

    fig = px.bar(
        dist,
        x=val_col,
        y="categoria",
        orientation="h",
        text="label",
        color_discrete_sequence=[cor],
        category_orders={"categoria": cats_order},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=max(300, len(dist) * 42 + 80),
        margin=dict(l=10, r=160, t=10, b=30),
        xaxis_title=x_label,
        yaxis_title="",
        yaxis=dict(type="category"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

    if analise["tipo"] == "top20":
        lookup = load_cnae_names() if analise["id"] == "cnae" else load_cbo_names()
        _show_lookup_table(dist["categoria"].tolist(), lookup)


# ── Renderiza todas as seções ─────────────────────────────────────────────────

for analise in ANALISES:
    render_analise(analise, grupo)
    st.divider()
