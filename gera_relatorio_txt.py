"""
Gera relatorio_distribuicao.txt com distribuições de CNAEs/campos por taxa 4,98%.
Executar: python distribuicao_nova_taxa/gera_relatorio_txt.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dados import ANALISES, get_grupo, load_data, distribuicao

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
OUT_FILE = OUT / "relatorio_distribuicao.txt"

# ── Helpers ───────────────────────────────────────────────────────────────────

BARRA_W = 30


def barra(valor: float, maximo: float) -> str:
    if maximo <= 0:
        return "░" * BARRA_W
    fill = round(BARRA_W * valor / maximo)
    return "█" * fill + "░" * (BARRA_W - fill)


def fmt_moeda(v: float) -> str:
    return f"R$ {v:>14,.2f}"


def fmt_int(v: float) -> str:
    return f"{int(v):>10,}"


GRUPOS = ["Todos", "Suspenso", "Aprovado"]
DIMS   = [
    ("contratos", "Por número de contratos", fmt_int),
    ("valor",     "Por valor de contratação (R$)", fmt_moeda),
]

# ── Carrega ───────────────────────────────────────────────────────────────────

print("Carregando dados…")
df = load_data()
print(f"  {len(df):,} contratos carregados (taxa 4,98%)")

# ── Geração ───────────────────────────────────────────────────────────────────

linhas: list[str] = []


def w(s: str = "") -> None:
    linhas.append(s)
    print(s)


w("=" * 78)
w("  RELATÓRIO TAXA 4,98% — DISTRIBUIÇÃO DE CONTRATOS")
w(f"  Total: {len(df):,} | Suspensos: {(df['Status do Processo']=='Suspenso').sum():,} | Aprovados: {(df['Status do Processo']=='Aprovado').sum():,}")
w("=" * 78)

for grupo in GRUPOS:
    df_view = get_grupo(df, grupo)
    n        = len(df_view)
    n_aprov  = (df_view["Status do Processo"] == "Aprovado").sum()
    n_susp   = (df_view["Status do Processo"] == "Suspenso").sum()
    val_tot  = df_view["_valor_contrat"].sum()

    w()
    w()
    w("▓" * 78)
    w(f"  GRUPO: {grupo.upper()}")
    w(f"  Contratos: {n:,}  |  Suspensos: {n_susp:,}  |  Aprovados: {n_aprov:,}")
    w(f"  Valor total contratado: R$ {val_tot:,.2f}")
    w("▓" * 78)

    for analise in ANALISES:
        w()
        w("─" * 78)
        w(f"  {analise['nome'].upper()}")
        if "obs" in analise:
            w(f"  [{analise['obs']}]")
        w("─" * 78)

        for dim_key, dim_label, fmt in DIMS:
            # Valor: pula se não há dados
            if dim_key == "valor" and df_view["_valor_contrat"].isna().all():
                w(f"\n  {dim_label}:")
                w("  (Dados de valor não disponíveis para este grupo)")
                continue

            dist = distribuicao(df_view, analise, dim_key)
            total_dim = dist["valor_dim"].sum()

            w()
            w(f"  {dim_label}  [total: {fmt(total_dim).strip()}]")
            w(f"  {'Categoria':<30}  {'Qtd/Valor':>16}  {'%':>6}  {'Distribuição'}")
            w(f"  {'─'*30}  {'─'*16}  {'─'*6}  {'─'*BARRA_W}")

            maximo = dist["valor_dim"].max()
            for _, row in dist.iterrows():
                cat = str(row["categoria"])[:30]
                val = row["valor_dim"]
                pct = row["pct"]
                bar = barra(val, maximo)
                w(f"  {cat:<30}  {fmt(val)}  {pct:>5.1f}%  {bar}")

w()
w("=" * 78)
w("  FIM DO RELATÓRIO")
w("=" * 78)

# ── Salva ─────────────────────────────────────────────────────────────────────

OUT_FILE.write_text("\n".join(linhas), encoding="utf-8")
print(f"\nRelatório salvo em: {OUT_FILE}")
