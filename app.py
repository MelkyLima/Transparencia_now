from __future__ import annotations

import gc
import logging
import os
from pathlib import Path
import sys
import time
import unicodedata

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TransparenciaApp")


def get_ram_usage_mb() -> float:
    """Return memory usage in MB safely across platforms."""
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    try:
        import resource

        rusage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return rusage / (1024 * 1024)
        return rusage / 1024
    except Exception:
        return 0.0


start_time = time.time()
ram_start = get_ram_usage_mb()
logger.info(f"🚀 Streamlit Rerun Iniciado | RAM Inicial: {ram_start:.1f} MB")

st.set_page_config(page_title="Painel Transparência TJRR", layout="wide")
st.markdown(
    """
<style>
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
* {
    user-select: text !important;
    -webkit-user-select: text !important;
}
.ind-card { border: 1px solid rgba(151,166,195,0.35); border-radius: 12px; padding: 16px 18px; background: rgba(20,28,45,0.45); }
.ind-card-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 10px; }
.ind-item { margin-bottom: 12px; }
.ind-label { font-size: 0.82rem; opacity: 0.85; margin-bottom: 2px; }
.ind-value { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }

.main-financial-grid {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 3.1fr) minmax(0, 1fr);
    gap: 16px;
    align-items: stretch;
}
.kpi-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
}
.tables-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px;
    flex-grow: 1;
}

@media (max-width: 991px) {
    .main-financial-grid {
        grid-template-columns: 1fr !important;
    }
}
@media (max-width: 640px) {
    .block-container {
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
    }
    .kpi-cards-grid {
        grid-template-columns: 1fr !important;
    }
    .tables-grid {
        grid-template-columns: 1fr !important;
    }
    .kpi-val-text {
        font-size: 1.15rem !important;
        word-break: break-word;
    }
}
/* Desabilitar autocomplete / autofill do navegador nos inputs do app */
input,
input[type="text"],
input[type="search"],
textarea {
    autocomplete: off !important;
}
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active,
textarea:-webkit-autofill {
    -webkit-box-shadow: 0 0 0px 1000px var(--background-color, #0e1117) inset !important;
    box-shadow: 0 0 0px 1000px var(--background-color, #0e1117) inset !important;
    transition: background-color 5000s ease-in-out 0s;
}
</style>
""",
    unsafe_allow_html=True,
)


# Inibir autocomplete/autofill do navegador nos campos do app
# Utiliza st.html (nova API) em vez de components.html para não gerar aviso de deprecação
st.html(
    """
    <script>
    (function() {
        function disableAutocomplete() {
            try {
                var doc = window.parent.document || window.document;
                doc.querySelectorAll('input, textarea, select').forEach(function(el) {
                    el.setAttribute('autocomplete', 'off');
                    el.setAttribute('autocorrect', 'off');
                    el.setAttribute('autocapitalize', 'none');
                    el.setAttribute('spellcheck', 'false');
                });
            } catch(e) {}
        }
        disableAutocomplete();
        var obs = new MutationObserver(disableAutocomplete);
        try {
            var doc = window.parent.document || window.document;
            obs.observe(doc.body, {childList: true, subtree: true});
        } catch(e) {}
    })();
    </script>
    """
)

def render_app_header(latest_update_str: str) -> str:
    """Render compact header bar with latest update date and technical source citation."""
    return (
        f'<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; padding: 10px 16px; background: rgba(20, 28, 45, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; margin-bottom: 12px; user-select: text !important; -webkit-user-select: text !important;">'
        f'<div style="display: flex; align-items: center; gap: 10px;">'
        f'<span style="width: 34px; height: 34px; border-radius: 10px; background: linear-gradient(135deg, #0284c7, #2563eb); display: inline-flex; align-items: center; justify-content: center; font-size: 1.1rem; color: white; box-shadow: 0 2px 8px rgba(2, 132, 199, 0.35);">🏛️</span>'
        f'<div>'
        f'<span style="font-size: 1.25rem; font-weight: 800; color: #ffffff; letter-spacing: -0.3px; line-height: 1.2; display: block;">Painel Transparência TJRR</span>'
        f'<span style="font-size: 0.76rem; color: #94a3b8; font-weight: 500;">Portal de Análise Remuneratória | Dados públicos extraídos do portal oficial <a href="https://remuneracoes.tjrr.jus.br" target="_blank" style="color: #38bdf8; text-decoration: underline; font-weight: 600;">remuneracoes.tjrr.jus.br</a></span>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; background: rgba(15, 23, 42, 0.7); padding: 5px 14px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.25);">'
        f'<span style="font-size: 0.78rem; color: #94a3b8; font-weight: 500;">Última atualização:</span>'
        f'<strong style="font-size: 0.82rem; color: #38bdf8; font-weight: 700;">{latest_update_str}</strong>'
        f'</div>'
        f'</div>'
    )


@st.cache_resource(show_spinner=False)
def load_cached(files: tuple[str, ...]):
    return load_all_dataframe([Path(p) for p in files])


@st.cache_data(show_spinner=False)
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Cache CSV string conversion so rapid filter reruns do not allocate memory repeatedly."""
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


@st.cache_resource(show_spinner=False)
def prepare_cached(df_raw: pd.DataFrame):
    """Cache expensive base transformations as a singleton resource without RAM duplication."""
    df = prepare_base_dataframe(df_raw)
    nome_col = pick_col(df, ["nome"]) or ("Nome" if "Nome" in df.columns else None)
    cargo_col = pick_col(df, ["cargo"]) or ("Cargo" if "Cargo" in df.columns else None)
    setor_col = pick_col(df, ["setor"]) or ("Setor" if "Setor" in df.columns else None)
    id_cols = [c for c in [nome_col, cargo_col, setor_col, "__vinculo", "__arquivo", "__arquivo_label", "__mes_plot", "__mes_dt", "__arquivo_ano"] if c and c in df.columns]
    value_cols = [c for c in df.columns if (not str(c).startswith("__")) and (c not in id_cols)]
    df_long, tipo_map = build_long_dataframe(df, id_cols=id_cols, value_cols=value_cols)

    # Prune unneeded columns in df_long to save RAM
    keep_cols = [c for c in [nome_col, cargo_col, setor_col, "__vinculo", "__arquivo_label", "__mes_dt", "__arquivo_ano", "TipoExib", "Valor"] if c in df_long.columns]
    df_long = df_long[keep_cols]

    gc.collect()
    return df, df_long, tipo_map, nome_col, cargo_col, setor_col, value_cols


@st.cache_data(show_spinner=False)
def format_detail_df(
    df_detail_base: pd.DataFrame,
    value_cols_tuple: tuple[str, ...],
    nome_col: str | None,
    cargo_col: str | None,
    setor_col: str | None,
    only_latest: bool = True,
    only_primary_cols: bool = True,
) -> pd.DataFrame:
    """Cache string formatting of detail table to prevent massive RAM allocations on reruns."""
    df_detail = df_detail_base
    if only_latest and nome_col and nome_col in df_detail.columns and "__mes_dt" in df_detail.columns:
        df_detail = df_detail.sort_values("__mes_dt").groupby(nome_col, as_index=False).last()

    df_detail = df_detail.copy()
    rename_map: dict[str, str] = {"__mes_plot": "Mês - Ano", "__arquivo": "Arquivo", "__vinculo": "Vínculo"}
    if nome_col:
        rename_map[nome_col] = "Nome"
    if cargo_col:
        rename_map[cargo_col] = "Cargo"
    if setor_col:
        rename_map[setor_col] = "Setor"
    for c in value_cols_tuple:
        if c in df_detail.columns:
            rename_map[c] = clean_tipo_label(c)
    df_detail = df_detail.rename(columns=rename_map)

    for c in value_cols_tuple:
        clean_c = clean_tipo_label(c)
        if clean_c in df_detail.columns:
            df_detail[clean_c] = coerce_ptbr_number(df_detail[clean_c]).map(format_brl)

    if "Nome" in df_detail.columns:
        df_detail["Nome"] = df_detail["Nome"].astype(str).str.strip()

        def _norm_sort(s: str) -> str:
            nfd = unicodedata.normalize("NFD", str(s))
            return "".join(c for c in nfd if unicodedata.category(c) != "Mn").upper()

        df_detail["__sort_nome"] = df_detail["Nome"].map(_norm_sort)
        df_detail = df_detail.sort_values(["Mês - Ano", "__sort_nome"], ascending=[False, True]).drop(columns=["__sort_nome"])
    else:
        df_detail = df_detail.sort_values(["Mês - Ano"], ascending=[False])

    if only_primary_cols:
        target_cols = [
            "Nome",
            "Cargo",
            "Remuneração Paradigma",
            "Subsídio, Função ou Cargo em Comissão",
            "Indenizações",
            "Total de Créditos",
            "Total de Débitos",
            "Rendimento Líquido",
            "Mês - Ano",
        ]
        existing_cols = [c for c in target_cols if c in df_detail.columns]
        if existing_cols:
            df_detail = df_detail[existing_cols]
    else:
        # Drop all redundant date and file metadata columns, keeping ONLY 'Mês - Ano'
        redundant_cols = [
            "Arquivo",
            "__arquivo",
            "__consulta_dt",
            "__mes_ref",
            "__mes_dt",
            "__arquivo_ano",
            "__arquivo_label",
        ]
        cols_to_drop = [c for c in df_detail.columns if c in redundant_cols or str(c).startswith("__")]
        if cols_to_drop:
            df_detail = df_detail.drop(columns=cols_to_drop)

    return df_detail


folder = Path(__file__).parent / "dados"
csv_files = list_csv_files(folder, recursive=False)
if not csv_files:
    st.warning(f"Nenhum CSV encontrado na pasta {folder}.")
    st.stop()

df_raw = load_cached(tuple(str(p) for p in csv_files))
df, df_long, tipo_map, nome_col, cargo_col, setor_col, value_cols = prepare_cached(df_raw)

latest_dt = df["__mes_dt"].max() if "__mes_dt" in df.columns else None
latest_update_str = (
    str(df.loc[df["__mes_dt"] == latest_dt, "__arquivo_label"].iloc[0])
    if (latest_dt is not None and "__arquivo_label" in df.columns and not df.loc[df["__mes_dt"] == latest_dt].empty)
    else "-"
)

st.html(render_app_header(latest_update_str))
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

def render_complete_financial_section(df_totais: pd.DataFrame, stats: dict[str, str]) -> str:
    """Render financial dashboard and Painel de Indenizações in a unified CSS Grid layout for 100% pixel-perfect height alignment."""
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
                f'<td style="padding: 9px 8px; font-size: 0.88rem; color: #e2e8f0; user-select: text !important; -webkit-user-select: text !important;">{tipo_str}</td>'
                f'<td style="padding: 9px 8px; font-size: 0.88rem; font-weight: 600; text-align: right; white-space: nowrap !important; color: #ffffff; user-select: text !important; -webkit-user-select: text !important;">{total_str.replace("R$ ", "R$&nbsp;")}</td>'
                f'</tr>'
            )
        else:
            entradas_rows_html += (
                f'<tr style="border-bottom: 1px solid rgba(151,166,195,0.12);">'
                f'<td style="padding: 9px 8px; font-size: 0.88rem; color: #e2e8f0; user-select: text !important; -webkit-user-select: text !important;">{tipo_str}</td>'
                f'<td style="padding: 9px 8px; font-size: 0.88rem; font-weight: 600; text-align: right; white-space: nowrap !important; color: #ffffff; user-select: text !important; -webkit-user-select: text !important;">{total_str.replace("R$ ", "R$&nbsp;")}</td>'
                f'</tr>'
            )

    no_ent = '<tr><td colspan="2" style="padding:10px; color:#94a3b8; font-size:0.85rem;">Nenhuma entrada registrada</td></tr>'
    no_sai = '<tr><td colspan="2" style="padding:10px; color:#94a3b8; font-size:0.85rem;">Nenhum desconto registrado</td></tr>'

    return (
        f'<div class="main-financial-grid" style="user-select: text !important; -webkit-user-select: text !important;">'
        f'<div style="display: flex; flex-direction: column; gap: 16px;">'
        f'<div class="kpi-cards-grid">'
        f'<div style="background: rgba(34, 197, 94, 0.06); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #16a34a; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">💼</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #86efac;">Total de Créditos</div>'
        f'<div class="kpi-val-text" style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px; white-space: nowrap !important;">{total_creditos_val.replace("R$ ", "R$&nbsp;")}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #4ade80; margin-top: 2px;">↑ Entradas</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #dc2626; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">⬇️</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #fca5a5;">Total de Débitos</div>'
        f'<div class="kpi-val-text" style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px; white-space: nowrap !important;">{total_debitos_val.replace("R$ ", "R$&nbsp;")}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #f87171; margin-top: 2px;">↓ Descontos</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(14, 165, 233, 0.06); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">'
        f'<div style="width: 44px; height: 44px; border-radius: 50%; background: #0284c7; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; flex-shrink: 0;">📊</div>'
        f'<div>'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #7dd3fc;">Rendimento Líquido</div>'
        f'<div class="kpi-val-text" style="font-size: 1.35rem; font-weight: 800; color: #ffffff; line-height: 1.2; margin-top: 2px; white-space: nowrap !important;">{rendimento_liquido_val.replace("R$ ", "R$&nbsp;")}</div>'
        f'<div style="font-size: 0.76rem; font-weight: 600; color: #38bdf8; margin-top: 2px;">↓ Valor recebido</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="tables-grid">'
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
        f'<div style="background: rgba(34, 197, 94, 0.15); border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; font-weight: 800; font-size: 0.95rem; color: #4ade80; margin-top: 12px;">'
        f'<span>Total de Créditos</span>'
        f'<span style="white-space: nowrap !important;">{total_creditos_val.replace("R$ ", "R$&nbsp;")}</span>'
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
        f'<div style="background: rgba(239, 68, 68, 0.15); border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; font-weight: 800; font-size: 0.95rem; color: #f87171; margin-top: 12px;">'
        f'<span>Total de Débitos</span>'
        f'<span style="white-space: nowrap !important;">{total_debitos_val.replace("R$ ", "R$&nbsp;")}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(20, 28, 45, 0.45); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; height: 100%;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px; padding-bottom: 12px; border-bottom: 1px solid rgba(56, 189, 248, 0.3); margin-bottom: 14px;">'
        f'<span style="width: 26px; height: 26px; border-radius: 50%; background: #0284c7; display: inline-flex; align-items: center; justify-content: center; font-size: 0.85rem; color: white;">🏖️</span>'
        f'<span style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">Painel de Indenizações</span>'
        f'</div>'
        f'<div style="display: flex; flex-direction: column; gap: 14px;">'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">Último registro ({stats["mes_label"]})</div>'
        f'<div style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-top: 2px; white-space: nowrap !important;">{stats["total_mes_atual"].replace("R$ ", "R$&nbsp;")}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">Total últimos 3 meses ({stats["meses_3m_label"]})</div>'
        f'<div style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-top: 2px; white-space: nowrap !important;">{stats["total_3m"].replace("R$ ", "R$&nbsp;")}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">Total deste ano ({stats["ano_recente"]})</div>'
        f'<div style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-top: 2px; white-space: nowrap !important;">{stats["total_ultimo_ano"].replace("R$ ", "R$&nbsp;")}</div>'
        f'</div>'
        f'<div style="padding-bottom: 10px; border-bottom: 1px solid rgba(151, 166, 195, 0.12);">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">Total ano anterior ({stats["ano_anterior"]})</div>'
        f'<div style="font-size: 1.45rem; font-weight: 800; color: #94a3b8; margin-top: 2px; white-space: nowrap !important;">{stats["total_ano_anterior"].replace("R$ ", "R$&nbsp;")}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: rgba(14, 165, 233, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 10px; padding: 12px 14px; margin-top: 16px;">'
        f'<div style="font-size: 0.82rem; font-weight: 600; color: #7dd3fc;">Total Geral (Indenizações)</div>'
        f'<div style="font-size: 1.55rem; font-weight: 800; color: #38bdf8; margin-top: 2px; white-space: nowrap !important;">{stats["inden_total"].replace("R$ ", "R$&nbsp;")}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


st.markdown("---")
st.subheader(f"Totais por tipo ({title_scope})")
totais_tipo = build_totais_tipo(df_f)
stats = build_indenizacao_stats(df_f, totais_tipo)
st.html(render_complete_financial_section(totais_tipo[["Tipo", "Total"]], stats))

st.markdown("---")
st.subheader("Gráficos de Créditos e Débitos")
c1, c2 = st.columns([1, 1])
with c1:
    fig_c = build_pie_figure(build_pizza_creditos(totais_tipo), "Créditos", height=655)
    if fig_c:
        st.plotly_chart(fig_c, width="stretch")
    else:
        st.info("Sem dados para montar a pizza de créditos.")
with c2:
    fig_d = build_pie_figure(build_pizza_debitos(totais_tipo), "Débitos", height=638)
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

st.subheader("Detalhamento dos dados")

c_opt1, c_opt2 = st.columns([1, 1])
with c_opt1:
    only_latest = st.checkbox("Exibir apenas último registro por servidor (Recomendado / Mais leve)", value=True)
with c_opt2:
    only_primary_cols = st.checkbox("Exibir apenas colunas principais", value=True)

df_export = format_detail_df(
    df_detail_base=df_detail_base,
    value_cols_tuple=tuple(value_cols),
    nome_col=nome_col,
    cargo_col=cargo_col,
    setor_col=setor_col,
    only_latest=only_latest,
    only_primary_cols=only_primary_cols,
)

st.dataframe(df_export, width="stretch", height=600, hide_index=True)

c_down_left, _ = st.columns([1, 3])
with c_down_left:
    csv_bytes = convert_df_to_csv(df_export)
    st.download_button(
        label="📥 Baixar Dados (CSV)",
        data=csv_bytes,
        file_name="dados_transparencia_filtrados.csv",
        mime="text/csv",
        width="stretch",
    )

elapsed_ms = (time.time() - start_time) * 1000
ram_end = get_ram_usage_mb()
logger.info(f"✅ Rerun Concluído com Sucesso em {elapsed_ms:.0f}ms | RAM Final: {ram_end:.1f} MB | Linhas Exibidas: {len(df_export)}")
gc.collect()