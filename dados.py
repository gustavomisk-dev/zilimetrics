"""
Carregamento e pré-processamento do Resultado_Relatorio_495.csv.
Importado por app_distribuicao.py e gera_relatorio_txt.py.
"""

import sys
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "Resultado_Relatorio_495.csv"


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_br_float(s):
    if pd.isna(s) or str(s).strip() == "":
        return None
    try:
        return float(str(s).strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def parse_data_atividade(s):
    """DDMMYYYY sem separadores → Timestamp."""
    if pd.isna(s) or str(s).strip() == "":
        return None
    v = str(s).strip().zfill(8)
    try:
        return pd.Timestamp(int(v[4:8]), int(v[2:4]), int(v[0:2]))
    except Exception:
        return None


# ── Faixas ────────────────────────────────────────────────────────────────────

def faixa_idade(y):
    if pd.isna(y):
        return "Não Informado"
    y = int(y)
    if y < 25:  return "< 25 anos"
    if y < 30:  return "25–29 anos"
    if y < 35:  return "30–34 anos"
    if y < 40:  return "35–39 anos"
    if y < 45:  return "40–44 anos"
    if y < 50:  return "45–49 anos"
    if y < 55:  return "50–54 anos"
    if y < 60:  return "55–59 anos"
    if y < 65:  return "60–64 anos"
    return "≥ 65 anos"


def faixa_valor_contrat(v):
    if pd.isna(v):        return "Não Informado"
    if v < 1_000:         return "< R$ 1.000"
    if v < 2_000:         return "R$ 1.000–2.000"
    if v < 3_000:         return "R$ 2.000–3.000"
    if v < 5_000:         return "R$ 3.000–5.000"
    if v < 10_000:        return "R$ 5.000–10.000"
    return "≥ R$ 10.000"


def faixa_num_emp(n):
    if pd.isna(n):    return "Não Informado"
    v = int(float(n))
    if v == 0:        return "Não Informado"
    if v == 1:        return "1"
    if v <= 6:        return "2–6"
    if v <= 10:       return "7–10"
    if v <= 20:       return "11–20"
    if v <= 50:       return "21–50"
    if v <= 100:      return "51–100"
    if v <= 500:      return "101–500"
    return "> 500"


def faixa_monetario(v):
    if pd.isna(v) or v <= 0: return "Não Informado"
    if v <= 50_000:           return "≤ R$ 50K"
    if v <= 100_000:          return "R$ 50K–100K"
    if v <= 250_000:          return "R$ 100K–250K"
    if v <= 500_000:          return "R$ 250K–500K"
    if v <= 1_000_000:        return "R$ 500K–1M"
    if v <= 2_500_000:        return "R$ 1M–2,5M"
    if v <= 5_000_000:        return "R$ 2,5M–5M"
    if v <= 10_000_000:       return "R$ 5M–10M"
    if v <= 25_000_000:       return "R$ 10M–25M"
    if v <= 50_000_000:       return "R$ 25M–50M"
    if v <= 100_000_000:      return "R$ 50M–100M"
    if v <= 500_000_000:      return "R$ 100M–500M"
    if v <= 1_000_000_000:    return "R$ 500M–1B"
    return "> R$ 1B"


def faixa_idade_empresa(y):
    if pd.isna(y):    return "Não Informado"
    y = float(y)
    if y < 2:         return "< 2 anos"
    if y < 5:         return "2–5 anos"
    if y < 10:        return "5–10 anos"
    if y < 20:        return "10–20 anos"
    if y < 30:        return "20–30 anos"
    return "≥ 30 anos"


def faixa_tempo_emp(m):
    if pd.isna(m):    return "Não Informado"
    m = int(float(m))
    if m < 6:         return "< 6 meses"
    if m < 12:        return "6–11 meses"
    if m < 24:        return "12–23 meses"
    if m < 48:        return "24–47 meses"
    if m < 60:        return "48–59 meses"
    if m < 120:       return "60–119 meses"
    return "≥ 120 meses"


def faixa_margem(p):
    if pd.isna(p):    return "Não Informado"
    if p <= 0:        return "≤ 0%"
    if p <= 10:       return "0–10%"
    if p <= 20:       return "10–20%"
    if p <= 30:       return "20–30%"
    if p <= 40:       return "30–40%"
    if p <= 50:       return "40–50%"
    if p <= 70:       return "50–70%"
    if p <= 100:      return "70–100%"
    return "> 100%"


def faixa_parcela(v):
    if pd.isna(v):    return "Não Informado"
    if v < 100:       return "< R$ 100"
    if v < 200:       return "R$ 100–200"
    if v < 300:       return "R$ 200–300"
    if v < 500:       return "R$ 300–500"
    if v < 1_000:     return "R$ 500–1.000"
    return "≥ R$ 1.000"


# ── Ordens canônicas ──────────────────────────────────────────────────────────

NI = "Não Informado"

ORDEM_IDADE = [
    "< 25 anos", "25–29 anos", "30–34 anos", "35–39 anos", "40–44 anos",
    "45–49 anos", "50–54 anos", "55–59 anos", "60–64 anos", "≥ 65 anos", NI,
]
ORDEM_VALOR_CONTRAT = [
    "< R$ 1.000", "R$ 1.000–2.000", "R$ 2.000–3.000",
    "R$ 3.000–5.000", "R$ 5.000–10.000", "≥ R$ 10.000", NI,
]
ORDEM_SEGURO   = ["Sim", "Não", NI]
ORDEM_PORTE    = ["EMPRESA DE PEQUENO PORTE", "DEMAIS", NI]
ORDEM_NUM_EMP  = ["1", "2–6", "7–10", "11–20", "21–50", "51–100", "101–500", "> 500", NI]
ORDEM_MONETARIO = [
    "≤ R$ 50K", "R$ 50K–100K", "R$ 100K–250K", "R$ 250K–500K",
    "R$ 500K–1M", "R$ 1M–2,5M", "R$ 2,5M–5M", "R$ 5M–10M",
    "R$ 10M–25M", "R$ 25M–50M", "R$ 50M–100M",
    "R$ 100M–500M", "R$ 500M–1B", "> R$ 1B", NI,
]
ORDEM_IDADE_EMP = ["< 2 anos", "2–5 anos", "5–10 anos", "10–20 anos", "20–30 anos", "≥ 30 anos", NI]
ORDEM_TEMPO_EMP = [
    "< 6 meses", "6–11 meses", "12–23 meses", "24–47 meses",
    "48–59 meses", "60–119 meses", "≥ 120 meses", NI,
]
ORDEM_MARGEM = ["≤ 0%", "0–10%", "10–20%", "20–30%", "30–40%", "40–50%", "50–70%", "70–100%", "> 100%", NI]
ORDEM_PARCELA = ["< R$ 100", "R$ 100–200", "R$ 200–300", "R$ 300–500", "R$ 500–1.000", "≥ R$ 1.000", NI]

# ── Definição das análises ────────────────────────────────────────────────────

ANALISES = [
    {
        "id": "idade",
        "nome": "Idade do Tomador",
        "coluna": "faixa_idade",
        "ordem": ORDEM_IDADE,
        "tipo": "faixa",
    },
    {
        "id": "valor_contrat",
        "nome": "Valor de Contratação",
        "coluna": "faixa_valor_contrat",
        "ordem": ORDEM_VALOR_CONTRAT,
        "tipo": "faixa",
        "obs": "Disponível apenas para Aprovados",
    },
    {
        "id": "seguro",
        "nome": "Seguro",
        "coluna": "seguro",
        "ordem": ORDEM_SEGURO,
        "tipo": "categoria",
    },
    {
        "id": "cbo",
        "nome": "CBO — Top 20",
        "coluna": "cbo",
        "ordem": None,
        "tipo": "top20",
        "obs": "Disponível apenas para Aprovados",
    },
    {
        "id": "cnae",
        "nome": "CNAE — Top 20",
        "coluna": "cnae",
        "ordem": None,
        "tipo": "top20",
    },
    {
        "id": "porte",
        "nome": "Porte da Empresa",
        "coluna": "porte",
        "ordem": ORDEM_PORTE,
        "tipo": "categoria",
    },
    {
        "id": "num_emp",
        "nome": "Número de Empregados",
        "coluna": "faixa_num_emp",
        "ordem": ORDEM_NUM_EMP,
        "tipo": "faixa",
    },
    {
        "id": "faturamento",
        "nome": "Faturamento da Empresa",
        "coluna": "faixa_faturamento",
        "ordem": ORDEM_MONETARIO,
        "tipo": "faixa",
    },
    {
        "id": "idade_empresa",
        "nome": "Idade da Empresa",
        "coluna": "faixa_idade_empresa",
        "ordem": ORDEM_IDADE_EMP,
        "tipo": "faixa",
        "obs": "Disponível apenas para Aprovados",
    },
    {
        "id": "capital",
        "nome": "Capital Social",
        "coluna": "faixa_capital",
        "ordem": ORDEM_MONETARIO,
        "tipo": "faixa",
    },
    {
        "id": "tempo_emp",
        "nome": "Tempo de Emprego",
        "coluna": "faixa_tempo_emp",
        "ordem": ORDEM_TEMPO_EMP,
        "tipo": "faixa",
    },
]


# ── Carregamento principal ────────────────────────────────────────────────────

def load_data(source=None) -> pd.DataFrame:
    if source is None:
        source = CSV_PATH
    df = pd.read_csv(source, sep=";", dtype=str)

    # Filtra taxa 4,98
    df = df[df["Taxa"].str.strip() == "4,98"].copy()

    # Datas de referência
    df["_dt_inicio"] = pd.to_datetime(df["Data de Início"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df["_dt_nasc"]   = pd.to_datetime(df["Data Nascimento"], format="%Y-%m-%d", errors="coerce")

    # Idade do tomador
    dias = (df["_dt_inicio"] - df["_dt_nasc"]).dt.days
    df["_idade"] = (dias / 365.25).where(df["_dt_inicio"].notna() & df["_dt_nasc"].notna())
    df["faixa_idade"] = df["_idade"].apply(faixa_idade)

    # Valor contratação
    df["_valor_contrat"] = df["Valor Contratação"].apply(parse_br_float)
    df["faixa_valor_contrat"] = df["_valor_contrat"].apply(faixa_valor_contrat)

    # Seguro
    def _seguro(s):
        if pd.isna(s) or str(s).strip() == "":
            return NI
        return "Sim" if str(s).strip().lower() == "true" else "Não"
    df["seguro"] = df["Possui Seguro"].apply(_seguro)

    # CBO
    df["cbo"] = df["CBO Código"].fillna(NI).str.strip().replace("", NI)

    # CNAE
    df["cnae"] = df["CNAE"].fillna(NI).str.strip().replace("", NI)

    # Porte
    df["porte"] = df["Porte Empresa"].fillna(NI).str.strip().replace("", NI)

    # Número de empregados
    df["_num_emp"] = pd.to_numeric(df["Número Empregados"], errors="coerce")
    df["faixa_num_emp"] = df["_num_emp"].apply(faixa_num_emp)

    # Faturamento
    df["_faturamento"] = df["Faturamento Empresa"].apply(parse_br_float)
    df["faixa_faturamento"] = df["_faturamento"].apply(faixa_monetario)

    # Idade da empresa (Data Início Atividade: DDMMYYYY)
    df["_dt_atividade"] = df["Data Início Atividade"].apply(parse_data_atividade)
    dias_emp = (df["_dt_inicio"] - df["_dt_atividade"]).dt.days
    df["_idade_empresa"] = (dias_emp / 365.25).where(
        df["_dt_inicio"].notna() & df["_dt_atividade"].notna()
    )
    df["faixa_idade_empresa"] = df["_idade_empresa"].apply(faixa_idade_empresa)

    # Capital Social
    df["_capital"] = df["Capital Social"].apply(parse_br_float)
    df["faixa_capital"] = df["_capital"].apply(faixa_monetario)

    # Tempo de emprego
    df["_tempo_emp"] = pd.to_numeric(df["Tempo Emprego Meses"], errors="coerce")
    df["faixa_tempo_emp"] = df["_tempo_emp"].apply(faixa_tempo_emp)

    # % Margem disponível
    df["_base_margem"] = df["Valor Base Margem"].apply(parse_br_float)
    df["_renda_liq"]   = df["Renda Líquida"].apply(parse_br_float)
    def _pct_margem(row):
        b, r = row["_base_margem"], row["_renda_liq"]
        if pd.isna(b) or pd.isna(r) or r == 0:
            return None
        return b / r * 100
    df["_pct_margem"] = df.apply(_pct_margem, axis=1)
    df["faixa_margem"] = df["_pct_margem"].apply(faixa_margem)

    # Valor da parcela
    df["_valor_parcela"] = df["ValorParcela"].apply(parse_br_float)
    df["faixa_parcela"] = df["_valor_parcela"].apply(faixa_parcela)

    return df


def get_grupo(df: pd.DataFrame, grupo: str) -> pd.DataFrame:
    if grupo == "Suspenso":
        return df[df["Status do Processo"] == "Suspenso"]
    if grupo == "Aprovado":
        return df[df["Status do Processo"] == "Aprovado"]
    return df


def distribuicao(df_view: pd.DataFrame, analise: dict, dim: str) -> pd.DataFrame:
    """
    Retorna DataFrame com colunas [categoria, valor, pct].
    dim: "contratos" | "valor"
    """
    col = analise["coluna"]
    ordem = analise["ordem"]
    tipo = analise["tipo"]

    if dim == "valor":
        agg = df_view.groupby(col, observed=True)["_valor_contrat"].sum().reset_index(name="valor")
        val_col = "valor"
    else:
        agg = df_view.groupby(col, observed=True).size().reset_index(name="contratos")
        val_col = "contratos"

    if ordem:
        template = pd.DataFrame({col: ordem})
        agg = template.merge(agg, on=col, how="left")
        agg[val_col] = agg[val_col].fillna(0)
        if dim == "valor":
            agg[val_col] = agg[val_col].astype(float)
        else:
            agg[val_col] = agg[val_col].astype(int)
    elif tipo == "top20":
        # Separa "Não Informado" do ranking, mostra top 20 reais + NI ao final
        ni_row = agg[agg[col] == NI]
        agg = agg[agg[col] != NI].sort_values(val_col, ascending=False).head(20)
        if not ni_row.empty:
            agg = pd.concat([agg, ni_row], ignore_index=True)
    else:
        agg = agg.sort_values(val_col, ascending=False)

    total = agg[val_col].sum()
    agg["pct"] = (agg[val_col] / total * 100).round(1) if total > 0 else 0.0
    agg = agg.rename(columns={col: "categoria", val_col: "valor_dim"})
    return agg.reset_index(drop=True)
