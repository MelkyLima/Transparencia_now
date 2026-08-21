from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import ALL_CATEGORIAS, ALL_VINCULOS, get_cargo_categoria


class FilterState:
    def __init__(
        self,
        anos_sel: list[str],
        arquivo_sel_label: str,
        nome_sel: list[str],
        categoria_sel: list[str],
        cargo_sel: list[str],
        vinculo_sel: list[str],
        setor_sel: list[str],
        tipo_sel: list[str],
    ):
        self.anos_sel = anos_sel
        self.arquivo_sel_label = arquivo_sel_label
        self.nome_sel = nome_sel
        self.categoria_sel = categoria_sel
        self.cargo_sel = cargo_sel
        self.vinculo_sel = vinculo_sel
        self.setor_sel = setor_sel
        self.tipo_sel = tipo_sel


def render_sidebar_filters(
    df: pd.DataFrame,
    df_long: pd.DataFrame,
    nome_col: str | None,
    cargo_col: str | None,
    setor_col: str | None,
) -> FilterState:
    """Render sidebar and return current selected filters with dynamic cascading options."""
    with st.sidebar:
        st.header("Filtros")

        # 1. Anos
        anos = sorted([str(int(a)) for a in df["__arquivo_ano"].dropna().unique().tolist()])
        anos_sel = st.multiselect("Ano(s) do arquivo", options=anos, default=anos, placeholder="Selecione ano(s)")

        df_sub = df
        df_long_sub = df_long

        if anos_sel:
            year_numeric = pd.to_numeric(pd.Series(anos_sel), errors="coerce").dropna().astype("Int64").tolist()
            df_sub = df_sub[df_sub["__arquivo_ano"].isin(year_numeric)]
            df_long_sub = df_long_sub[df_long_sub["__arquivo_ano"].isin(year_numeric)]

        # 2. Busca por Arquivo
        arquivos_df = df_sub[["__arquivo", "__arquivo_label", "__arquivo_ano", "__mes_dt"]].drop_duplicates()
        arquivos_df = arquivos_df.sort_values(["__mes_dt", "__arquivo"])
        arquivo_labels = arquivos_df["__arquivo_label"].dropna().astype(str).tolist()
        arquivo_sel_label = st.selectbox("Busca por Arquivo", options=["Todos"] + arquivo_labels, index=0)

        if arquivo_sel_label != "Todos":
            df_sub = df_sub[df_sub["__arquivo_label"] == arquivo_sel_label]
            df_long_sub = df_long_sub[df_long_sub["__arquivo_label"] == arquivo_sel_label]

        # 3. Busca por Nome (se houver nome selecionado, restringe os demais campos aos dados daquela pessoa)
        nomes_opts = sorted(df_sub[nome_col].dropna().astype(str).unique().tolist()) if nome_col and nome_col in df_sub.columns else []
        nome_sel = st.multiselect(
            "Busca por Nome",
            options=nomes_opts,
            default=[],
            placeholder="Digite para buscar nome(s)",
        )
        if nome_sel and nome_col and nome_col in df_sub.columns:
            df_sub = df_sub[df_sub[nome_col].astype(str).isin(nome_sel)]
            df_long_sub = df_long_sub[df_long_sub[nome_col].astype(str).isin(nome_sel)]

        # 4. Nível / Categoria do Cargo
        cats_in_df = df_sub[cargo_col].astype(str).map(get_cargo_categoria) if cargo_col and cargo_col in df_sub.columns else pd.Series(dtype=str)
        avail_cats = [c for c in ALL_CATEGORIAS if c in cats_in_df.unique()]
        categoria_sel = st.multiselect(
            "Nível / Categoria do Cargo",
            options=avail_cats,
            default=[],
            placeholder="Selecione categoria(s)",
        )
        if categoria_sel:
            mask_cat = cats_in_df.isin(categoria_sel)
            df_sub = df_sub[mask_cat]
            if cargo_col and cargo_col in df_long_sub.columns:
                df_long_sub = df_long_sub[df_long_sub[cargo_col].astype(str).map(get_cargo_categoria).isin(categoria_sel)]

        # 5. Filtro por Vínculo
        vincs_in_df = df_sub["__vinculo"].dropna().unique().tolist() if "__vinculo" in df_sub.columns else []
        avail_vincs = [v for v in ALL_VINCULOS if v in vincs_in_df]
        vinculo_sel = st.multiselect(
            "Filtro por Vínculo",
            options=avail_vincs,
            default=[],
            placeholder="Selecione vínculo(s)",
        )
        if vinculo_sel and "__vinculo" in df_sub.columns:
            df_sub = df_sub[df_sub["__vinculo"].isin(vinculo_sel)]
            if "__vinculo" in df_long_sub.columns:
                df_long_sub = df_long_sub[df_long_sub["__vinculo"].isin(vinculo_sel)]

        # 6. Filtro por Cargo
        cargos_opts = sorted(df_sub[cargo_col].dropna().astype(str).unique().tolist()) if cargo_col and cargo_col in df_sub.columns else []
        cargo_sel = st.multiselect("Filtro por Cargo", options=cargos_opts, default=[], placeholder="Selecione cargo(s)")
        if cargo_sel and cargo_col and cargo_col in df_sub.columns:
            df_sub = df_sub[df_sub[cargo_col].astype(str).isin(cargo_sel)]
            if cargo_col in df_long_sub.columns:
                df_long_sub = df_long_sub[df_long_sub[cargo_col].astype(str).isin(cargo_sel)]

        # 7. Filtro por Setor
        setor_opts = sorted(df_sub[setor_col].dropna().astype(str).unique().tolist()) if setor_col and setor_col in df_sub.columns else []
        setor_sel = st.multiselect("Filtro por Setor", options=setor_opts, default=[], placeholder="Selecione setor(es)")
        if setor_sel and setor_col and setor_col in df_sub.columns:
            df_sub = df_sub[df_sub[setor_col].astype(str).isin(setor_sel)]
            if setor_col in df_long_sub.columns:
                df_long_sub = df_long_sub[df_long_sub[setor_col].astype(str).isin(setor_sel)]

        # 8. Busca por Tipo
        tipos_opts = sorted(df_long_sub["TipoExib"].dropna().astype(str).unique().tolist()) if "TipoExib" in df_long_sub.columns else []
        todos_tipos = st.checkbox("Todos os tipos", value=True)
        tipo_sel = st.multiselect("Busca por Tipo", options=tipos_opts, default=[], placeholder="Selecione tipo(s)") if not todos_tipos else tipos_opts

    return FilterState(
        anos_sel=anos_sel,
        arquivo_sel_label=arquivo_sel_label,
        nome_sel=nome_sel,
        categoria_sel=categoria_sel,
        cargo_sel=cargo_sel,
        vinculo_sel=vinculo_sel,
        setor_sel=setor_sel,
        tipo_sel=tipo_sel,
    )

