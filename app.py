from __future__ import annotations

from pathlib import Path

import streamlit as st

from charts import (
    build_evolucao_dataframe,
    build_evolucao_figure,
    build_indenizacao_stats,
    build_pie_figure,
    build_pizza_creditos,
    build_pizza_debitos,
    build_totais_tipo,
)
from data_loader import list_csv_files, load_all_dataframe
from filters import render_sidebar_filters
from transformations import (
    build_long_dataframe,
    filter_detail_dataframe,
    filter_long_dataframe,
    prepare_base_dataframe,
)
from utils import clean_tipo_label, coerce_ptbr_number, format_brl, pick_col


st.set_page_config(page_title="Painel CSV", layout="wide")
st.markdown(
    """
<style>
.ind-card { border: 1px solid rgba(151,166,195,0.35); border-radius: 12px; padding: 16px 18px; background: rgba(20,28,45,0.45); }
.ind-card-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 10px; }
.ind-item { margin-bottom: 12px; }
.ind-label { font-size: 0.82rem; opacity: 0.85; margin-bottom: 2px; }
.ind-value { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Painel Transparência TJRR")


@st.cache_data(show_spinner=False)
def load_cached(files: tuple[str, ...]):
    return load_all_dataframe([Path(p) for p in files])


@st.cache_data(show_spinner=False)
def prepare_cached(df_raw):
    """Cache expensive base transformations independent from UI filters."""
    df = prepare_base_dataframe(df_raw)
    nome_col = pick_col(df, ["nome"]) or ("Nome" if "Nome" in df.columns else None)
    cargo_col = pick_col(df, ["cargo"]) or ("Cargo" if "Cargo" in df.columns else None)
    setor_col = pick_col(df, ["setor"]) or ("Setor" if "Setor" in df.columns else None)
    id_cols = [c for c in [nome_col, cargo_col, setor_col, "__arquivo", "__arquivo_label", "__mes_plot", "__mes_dt", "__arquivo_ano"] if c and c in df.columns]
    value_cols = [c for c in df.columns if (not str(c).startswith("__")) and (c not in id_cols)]
    df_long, tipo_map = build_long_dataframe(df, id_cols=id_cols, value_cols=value_cols)
    return df, df_long, tipo_map, nome_col, cargo_col, setor_col, value_cols


folder = Path.cwd() /"dados"
csv_files = list_csv_files(folder, recursive=False)
if not csv_files:
    st.warning("Nenhum CSV encontrado nessa pasta.")
    st.stop()

df_raw = load_cached(tuple(str(p) for p in csv_files))
st.caption(f"Arquivos lidos: {len(csv_files)} | Linhas: {len(df_raw):,}".replace(",", "."))

df, df_long, tipo_map, nome_col, cargo_col, setor_col, value_cols = prepare_cached(df_raw)
state = render_sidebar_filters(df=df, df_long=df_long, nome_col=nome_col, cargo_col=cargo_col, setor_col=setor_col)

df_f = filter_long_dataframe(
    df_long=df_long,
    anos_sel=state.anos_sel,
    arquivo_sel_label=state.arquivo_sel_label,
    nome_sel=state.nome_sel,
    nome_col=nome_col,
    cargo_sel=state.cargo_sel,
    cargo_col=cargo_col,
    setor_sel=state.setor_sel,
    setor_col=setor_col,
    tipo_sel=state.tipo_sel,
)
df_detail_base = filter_detail_dataframe(
    df=df,
    anos_sel=state.anos_sel,
    arquivo_sel_label=state.arquivo_sel_label,
    nome_sel=state.nome_sel,
    nome_col=nome_col,
    cargo_sel=state.cargo_sel,
    cargo_col=cargo_col,
    setor_sel=state.setor_sel,
    setor_col=setor_col,
    tipo_sel=state.tipo_sel,
    tipo_map=tipo_map,
)

title_scope = "Todos"
if state.nome_sel and nome_col and nome_col in df_f.columns:
    found_names = sorted(df_f[nome_col].dropna().astype(str).str.strip().loc[lambda s: s.ne("")].unique().tolist())
    if len(found_names) == 1:
        title_scope = found_names[0]
    elif len(found_names) > 1:
        title_scope = ", ".join(found_names[:3]) + ("..." if len(found_names) > 3 else "")

st.markdown("---")
st.subheader(f"Totais por tipo ({title_scope})")
totais_tipo = build_totais_tipo(df_f)
left, right = st.columns([1, 1])
with left:
    table_h = max(260, 38 * len(totais_tipo))
    st.dataframe(totais_tipo[["Tipo", "Total"]], use_container_width=True, height=table_h, hide_index=True)
with right:
    stats = build_indenizacao_stats(df_f, totais_tipo)
    st.markdown(
        f"""
<div class="ind-card">
  <div class="ind-card-title">Painel de Indenizações</div>
  <div class="ind-item"><div class="ind-label">Último registro ({stats["mes_label"]})</div><div class="ind-value">{stats["total_mes_atual"]}</div></div>
  <div class="ind-item"><div class="ind-label">Total últimos 3 meses ({stats["meses_3m_label"]})</div><div class="ind-value">{stats["total_3m"]}</div></div>
  <div class="ind-item"><div class="ind-label">Total deste ano ({stats["ano_recente"]})</div><div class="ind-value">{stats["total_ultimo_ano"]}</div></div>
  <div class="ind-item"><div class="ind-label">Total ano anterior ({stats["ano_anterior"]})</div><div class="ind-value">{stats["total_ano_anterior"]}</div></div>
  <div class="ind-item"><div class="ind-label">Total Geral</div><div class="ind-value">{stats["inden_total"]}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("---")
st.subheader("Gráficos de Créditos e Débitos")
c1, c2 = st.columns([1, 1])
with c1:
    fig_c = build_pie_figure(build_pizza_creditos(totais_tipo), "Créditos")
    if fig_c:
        st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("Sem dados para montar a pizza de créditos.")
with c2:
    fig_d = build_pie_figure(build_pizza_debitos(totais_tipo), "Débitos")
    if fig_d:
        st.plotly_chart(fig_d, use_container_width=True)
    else:
        st.info("Sem dados para montar a pizza de débitos.")

st.markdown("---")
modo_evol = st.radio("Gráfico de Evolução", options=["mês a mês", "ano a ano"], horizontal=True)
granularidade = "mes" if modo_evol == "mês a mês" else "ano"
st.subheader(f"Gráfico de Evolução ({modo_evol})")
evol, tipo_ordem = build_evolucao_dataframe(df_f, granularidade=granularidade)
fig_evol = build_evolucao_figure(evol, tipo_ordem, granularidade=granularidade)
if fig_evol:
    st.plotly_chart(fig_evol, use_container_width=True)
else:
    st.info("Sem dados para evolução mês a mês com os filtros atuais.")

st.markdown("---")
st.subheader("Detalhamento dos dados")
df_detail = df_detail_base.copy()
rename_map: dict[str, str] = {"__mes_plot": "Mês - Ano", "__arquivo": "Arquivo"}
if nome_col:
    rename_map[nome_col] = "Nome"
if cargo_col:
    rename_map[cargo_col] = "Cargo"
if setor_col:
    rename_map[setor_col] = "Setor"
for c in value_cols:
    if c in df_detail.columns:
        rename_map[c] = clean_tipo_label(c)
df_detail = df_detail.rename(columns=rename_map)
for c in value_cols:
    if c in df_detail.columns:
        # Convert only filtered rows, not full source dataset.
        df_detail[c] = coerce_ptbr_number(df_detail[c]).map(format_brl)
st.dataframe(df_detail.sort_values(["Mês - Ano"], ascending=[True]), use_container_width=False, height=600, hide_index=True)