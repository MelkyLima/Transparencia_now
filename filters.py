from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


from utils import ALL_CATEGORIAS, get_cargo_categoria


@dataclass
class FilterState:
    anos_sel: list[str]
    arquivo_sel_label: str
    nome_sel: list[str]
    categoria_sel: list[str]
    cargo_sel: list[str]
    setor_sel: list[str]
    tipo_sel: list[str]


def render_sidebar_filters(
    df: pd.DataFrame,
    df_long: pd.DataFrame,
    nome_col: str | None,
    cargo_col: str | None,
    setor_col: str | None,
) -> FilterState:
    """Render sidebar and return current selected filters."""
    with st.sidebar:
        st.header("Filtros")
        anos = sorted([str(int(a)) for a in df["__arquivo_ano"].dropna().unique().tolist()])
        anos_sel = st.multiselect("Ano(s) do arquivo", options=anos, default=anos, placeholder="Selecione ano(s)")

        arquivos_df = df[["__arquivo", "__arquivo_label", "__arquivo_ano", "__mes_dt"]].drop_duplicates()
        if anos_sel:
            year_numeric = pd.to_numeric(pd.Series(anos_sel), errors="coerce").dropna().astype("Int64")
            arquivos_df = arquivos_df[arquivos_df["__arquivo_ano"].isin(year_numeric)]
        arquivos_df = arquivos_df.sort_values(["__mes_dt", "__arquivo"])
        arquivo_labels = arquivos_df["__arquivo_label"].dropna().astype(str).tolist()
        arquivo_sel_label = st.selectbox("Busca por Arquivo", options=["Todos"] + arquivo_labels, index=0)

        nome_sel: list[str] = []
        if nome_col and nome_col in df_long.columns:
            nomes_base = sorted(df_long[nome_col].dropna().astype(str).unique().tolist())
            nome_sel = st.multiselect(
                "Busca por Nome",
                options=nomes_base,
                default=[],
                placeholder="Digite para buscar nome(s)",
            )

        cargos_base = sorted(df_long[cargo_col].dropna().astype(str).unique().tolist()) if cargo_col and cargo_col in df_long.columns else []
        categoria_sel = st.multiselect(
            "Nível / Categoria do Cargo",
            options=ALL_CATEGORIAS,
            default=[],
            placeholder="Selecione categoria(s)",
        )

        if categoria_sel:
            cargos_filtrados = [c for c in cargos_base if get_cargo_categoria(c) in categoria_sel]
        else:
            cargos_filtrados = cargos_base

        cargo_sel = st.multiselect("Filtro por Cargo", options=cargos_filtrados, default=[], placeholder="Selecione cargo(s)")

        setor_opts = sorted(df_long[setor_col].dropna().astype(str).unique().tolist()) if setor_col and setor_col in df_long.columns else []
        setor_sel = st.multiselect("Filtro por Setor", options=setor_opts, default=[], placeholder="Selecione setor(es)")

        tipos = sorted(df_long["TipoExib"].dropna().astype(str).unique().tolist())
        todos_tipos = st.checkbox("Todos os tipos", value=True)
        tipo_sel = st.multiselect("Busca por Tipo", options=tipos, default=[], placeholder="Selecione tipo(s)") if not todos_tipos else tipos

    return FilterState(
        anos_sel=anos_sel,
        arquivo_sel_label=arquivo_sel_label,
        nome_sel=nome_sel,
        categoria_sel=categoria_sel,
        cargo_sel=cargo_sel,
        setor_sel=setor_sel,
        tipo_sel=tipo_sel,
    )

