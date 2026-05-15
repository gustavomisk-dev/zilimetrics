"""
Streamlit — Distribuição de contratos taxa 4,98%.
Executar: streamlit run distribuicao_nova_taxa/app_distribuicao.py
"""

import sys
from pathlib import Path

import io
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from dados import ANALISES, get_grupo, load_data, distribuicao

# ── Config ────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Taxa 4,98% — Distribuição",
    page_icon="📊",
    layout="wide",
)

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
    url = "https://raw.githubusercontent.com/datasets-br/cbo/master/data/cbo.csv"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        cbo_df = pd.read_csv(io.StringIO(r.text), dtype=str)
        PRIO = {"Ocupacao": 0, "Sinônimo": 1, "Família": 2}
        best: dict = {}
        family: dict = {}
        for _, row in cbo_df.iterrows():
            cod = str(row.get("codigo", "")).strip()
            tipo = str(row.get("tipo", "")).strip()
            titulo = str(row.get("titulo", "")).strip()
            if not cod or not titulo:
                continue
            prio = PRIO.get(tipo, 99)
            if tipo == "Família":
                family[cod[:4]] = titulo
            cur = best.get(cod)
            if cur is None or prio < cur[0]:
                best[cod] = (prio, titulo)
        result = {cod: val[1] for cod, val in best.items()}
        result["_family"] = family
        return result
    except Exception:
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


uploaded = st.file_uploader(
    "Faça upload do relatório CSV (sep `;`)",
    type="csv",
    label_visibility="collapsed",
)

if uploaded is None:
    st.info("⬆️ Faça o upload do arquivo CSV para começar.")
    st.stop()

df = _load(uploaded.read())

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Filtros")
    grupo = st.radio(
        "Grupo",
        ["Todos", "Suspenso", "Aprovado"],
        index=0,
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

    with st.expander("Ver tabela", expanded=False):
        show = dist[["categoria", val_col, "pct"]].copy()
        show.columns = [analise["nome"], x_label, "% do Total"]
        if fmt_moeda:
            show[x_label] = show[x_label].apply(lambda v: f"R$ {v:,.2f}")
        else:
            show[x_label] = show[x_label].apply(lambda v: f"{int(v):,}")
        show["% do Total"] = show["% do Total"].apply(lambda v: f"{v:.1f}%")
        st.dataframe(show, hide_index=True, use_container_width=True, key=f"{key}_tbl")


# ── Renderiza todas as seções ─────────────────────────────────────────────────

for analise in ANALISES:
    render_analise(analise, grupo)
    st.divider()
