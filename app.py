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
* {
    user-select: text !important;
    -webkit-user-select: text !important;
}
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
    id_cols = [c for c in [nome_col, cargo_col, setor_col, "__vinculo", "__arquivo", "__arquivo_label", "__mes_plot", "__mes_dt", "__arquivo_ano"] if c and c in df.columns]
    value_cols = [c for c in df.columns if (not str(c).startswith("__")) and (c not in id_cols)]
    df_long, tipo_map = build_long_dataframe(df, id_cols=id_cols, value_cols=value_cols)
    return df, df_long, tipo_map, nome_col, cargo_col, setor_col, value_cols


folder = Path(__file__).parent / "dados"
csv_files = list_csv_files(folder, recursive=False)
if not csv_files:
    st.warning(f"Nenhum CSV encontrado na pasta {folder}.")
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
    categoria_sel=state.categoria_sel,
    cargo_sel=state.cargo_sel,
    cargo_col=cargo_col,
    vinculo_sel=state.vinculo_sel,
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
    categoria_sel=state.categoria_sel,
    cargo_sel=state.cargo_sel,
    cargo_col=cargo_col,
    vinculo_sel=state.vinculo_sel,
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

def render_financial_dashboard(df_totais: pd.DataFrame) -> str:
    """Render financial dashboard with 3 top summary cards and 2 detailed tables matching reference mockup."""
    entradas_rows_html = ""
    saidas_rows_html = ""

    total_creditos_val = "R$ 0,00"
    total_debitos_val = "R$ 0,00"
    rendimento_liquido_val = "R$ 0,00"

    saidas_patterns = ["imposto", "previdência", "previdencia", "desconto", "teto"]

    for _, row in df_totais.iterrows():
        tipo_str = str(row["Tipo"])
        total_str = str(row["Total"])
        t_lower = tipo_str.lower()

        if "total de créditos" in t_lower or "total de creditos" in t_lower:
            total_creditos_val = total_str
        elif "total de débitos" in t_lower or "total de debitos" in t_lower:
            total_debitos_val = total_str
        elif "líquido" in t_lower or "liquido" in t_lower:
            rendimento_liquido_val = total_str
        elif any(p in t_lower for p in saidas_patterns) or "débito" in t_lower or "debit" in t_lower:
            saidas_rows_html += (
                f'<tr style="border-bottom: 1px solid rgba(151,166,195,0.12);">'
                f'<td style="padding: 9px 12px; font-size: 0.88rem; color: #e2e8f0; user-select: text !important; -webkit-user-select: text !important;">{tipo_str}</td>'
                f'<td style="padding: 9px 12px; font-size: 0.88rem; font-weight: 600; text-align: right; color: #ffffff; user-select: text !important; -webkit-user-select: text !important;">{total_str}</td>'
                f'</tr>'
            )
        else:
            entradas_rows_html += (
                f'<tr style="border-bottom: 1px solid rgba(151,166,195,0.12);">'
                f'<td style="padding: 9px 12px; font-size: 0.88rem; color: #e2e8f0; user-select: text !important; -webkit-user-select: text !important;">{tipo_str}</td>'
                f'<td style="padding: 9px 12px; font-size: 0.88rem; font-weight: 600; text-align: right; color: #ffffff; user-select: text !important; -webkit-user-select: text !important;">{total_str}</td>'
                f'</tr>'
            )

    no_ent = '<tr><td colspan="2" style="padding:10px; color:#94a3b8; font-size:0.85rem;">Nenhuma entrada registrada</td></tr>'
    no_sai = '<tr><td colspan="2" style="padding:10px; color:#94a3b8; font-size:0.85rem;">Nenhum desconto registrado</td></tr>'

    return (
        f'<div style="width: 100%; display: flex; flex-direction: column; gap: 16px; user-select: text !important; -webkit-user-select: text !important;">'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px;">'
        f'<div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #16a34a; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">💼</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #86efac;">Total de Créditos</div>'
        f'<div style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px;">{total_creditos_val}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #4ade80; margin-top: 2px;">↑ Entradas</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #dc2626; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">⬇️</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #fca5a5;">Total de Débitos</div>'
        f'<div style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px;">{total_debitos_val}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #f87171; margin-top: 2px;">↓ Descontos</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(14, 165, 233, 0.06); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #0284c7; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">📊</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #7dd3fc;">Rendimento Líquido</div>'
        f'<div style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px;">{rendimento_liquido_val}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #38bdf8; margin-top: 2px;">↓ Valor recebido</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">'
        f'<div style="background: rgba(20, 28, 45, 0.45); border: 1px solid rgba(34, 197, 94, 0.35); border-radius: 14px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div>'
        f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(34, 197, 94, 0.12); border-radius: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 0.95rem; font-weight: 700; color: #4ade80; display: flex; align-items: center; gap: 8px;">'
        f'<span style="width: 24px; height: 24px; border-radius: 50%; background: #22c55e; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; color: white;">🟢</span>'
        f'Entradas / Créditos'
        f'</span>'
        f'<span style="font-size: 0.82rem; font-weight: 600; color: #94a3b8;">Valor</span>'
        f'</div>'
        f'<table style="width: 100%; border-collapse: collapse;">'
        f'<tbody>'
        f'{entradas_rows_html or no_ent}'
        f'</tbody>'
        f'</table>'
        f'</div>'
        f'<div style="background: rgba(34, 197, 94, 0.15); border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; font-weight: 800; font-size: 0.95rem; color: #4ade80; margin-top: 12px;">'
        f'<span>Total de Créditos</span>'
        f'<span>{total_creditos_val}</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(20, 28, 45, 0.45); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 14px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div>'
        f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(239, 68, 68, 0.12); border-radius: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 0.95rem; font-weight: 700; color: #f87171; display: flex; align-items: center; gap: 8px;">'
        f'<span style="width: 24px; height: 24px; border-radius: 50%; background: #ef4444; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; color: white;">⬇️</span>'
        f'Saídas / Descontos'
        f'</span>'
        f'<span style="font-size: 0.82rem; font-weight: 600; color: #94a3b8;">Valor</span>'
        f'</div>'
        f'<table style="width: 100%; border-collapse: collapse;">'
        f'<tbody>'
        f'{saidas_rows_html or no_sai}'
        f'</tbody>'
        f'</table>'
        f'</div>'
        f'<div style="background: rgba(239, 68, 68, 0.15); border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; font-weight: 800; font-size: 0.95rem; color: #f87171; margin-top: 12px;">'
        f'<span>Total de Débitos</span>'
        f'<span>{total_debitos_val}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def render_indenizacao_card(stats: dict[str, str]) -> str:
    """Render Painel de Indenizações spanning 100% height with matching visual elements."""
    return (
        f'<div style="height: 100%; min-height: 535px; background: rgba(20, 28, 45, 0.45); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; user-select: text !important; -webkit-user-select: text !important;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px; padding-bottom: 12px; border-bottom: 1px solid rgba(56, 189, 248, 0.3); margin-bottom: 16px;">'
        f'<span style="width: 28px; height: 28px; border-radius: 50%; background: #0284c7; display: inline-flex; align-items: center; justify-content: center; font-size: 0.9rem; color: white;">🏖️</span>'
        f'<span style="font-size: 1.08rem; font-weight: 700; color: #ffffff;">Painel de Indenizações</span>'
        f'</div>'
        f'<div style="display: flex; flex-direction: column; gap: 16px;">'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">Último registro ({stats["mes_label"]})</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{stats["total_mes_atual"]}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">Total últimos 3 meses ({stats["meses_3m_label"]})</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{stats["total_3m"]}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">Total deste ano ({stats["ano_recente"]})</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{stats["total_ultimo_ano"]}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.82rem; color: #94a3b8; font-weight: 500;">Total ano anterior ({stats["ano_anterior"]})</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #94a3b8; margin-top: 2px;">{stats["total_ano_anterior"]}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(14, 165, 233, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 14px 16px; margin-top: 18px;">'
        f'<div style="font-size: 0.84rem; font-weight: 600; color: #7dd3fc;">Total Geral (Indenizações)</div>'
        f'<div style="font-size: 1.6rem; font-weight: 800; color: #38bdf8; margin-top: 2px;">{stats["inden_total"]}</div>'
        f'</div>'
        f'</div>'
    )


st.markdown("---")
st.subheader(f"Totais por tipo ({title_scope})")
totais_tipo = build_totais_tipo(df_f)
left, right = st.columns([3, 1])
with left:
    st.html(render_financial_dashboard(totais_tipo[["Tipo", "Total"]]))
with right:
    stats = build_indenizacao_stats(df_f, totais_tipo)
    st.html(render_indenizacao_card(stats))

st.markdown("---")
st.subheader("Gráficos de Créditos e Débitos")
c1, c2 = st.columns([1, 1])
with c1:
    fig_c = build_pie_figure(build_pizza_creditos(totais_tipo), "Créditos")
    if fig_c:
        st.plotly_chart(fig_c, width="stretch")
    else:
        st.info("Sem dados para montar a pizza de créditos.")
with c2:
    fig_d = build_pie_figure(build_pizza_debitos(totais_tipo), "Débitos")
    if fig_d:
        st.plotly_chart(fig_d, width="stretch")
    else:
        st.info("Sem dados para montar a pizza de débitos.")

st.markdown("---")
modo_evol = st.radio("Gráfico de Evolução", options=["mês a mês", "ano a ano"], horizontal=True)
granularidade = "mes" if modo_evol == "mês a mês" else "ano"
st.subheader(f"Gráfico de Evolução ({modo_evol})")
evol, tipo_ordem = build_evolucao_dataframe(df_f, granularidade=granularidade)
fig_evol = build_evolucao_figure(evol, tipo_ordem, granularidade=granularidade)
if fig_evol:
    st.plotly_chart(fig_evol, width="stretch")
else:
    st.info("Sem dados para evolução mês a mês com os filtros atuais.")

st.markdown("---")
df_detail = df_detail_base.copy()
rename_map: dict[str, str] = {"__mes_plot": "Mês - Ano", "__arquivo": "Arquivo", "__vinculo": "Vínculo"}
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

col_det_title, col_det_down = st.columns([3, 1])
df_export = df_detail.sort_values(["Mês - Ano"], ascending=[True])
with col_det_title:
    st.subheader("Detalhamento dos dados")
with col_det_down:
    csv_bytes = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar Dados (CSV)",
        data=csv_bytes,
        file_name="dados_transparencia_filtrados.csv",
        mime="text/csv",
        width="stretch",
    )
st.dataframe(df_export, width="stretch", height=600, hide_index=True)