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


def get_filtered_df(
    df: pd.DataFrame,
    nome_col: str | None,
    cargo_col: str | None,
    setor_col: str | None,
    anos_sel: list[str] | None = None,
    arquivo_sel_label: str | None = None,
    nome_sel: list[str] | None = None,
    categoria_sel: list[str] | None = None,
    vinculo_sel: list[str] | None = None,
    cargo_sel: list[str] | None = None,
    setor_sel: list[str] | None = None,
) -> pd.DataFrame:
    """Filter dataframe by active selections, optionally omitting one filter."""
    out = df
    if anos_sel:
        y_num = pd.to_numeric(pd.Series(anos_sel), errors="coerce").dropna().astype("Int64").tolist()
        out = out[out["__arquivo_ano"].isin(y_num)]
    if arquivo_sel_label and arquivo_sel_label != "Todos":
        out = out[out["__arquivo_label"] == arquivo_sel_label]
    if nome_sel and nome_col and nome_col in out.columns:
        out = out[out[nome_col].astype(str).isin(nome_sel)]
    if categoria_sel and cargo_col and cargo_col in out.columns:
        cats = out[cargo_col].astype(str).map(get_cargo_categoria)
        out = out[cats.isin(categoria_sel)]
    if vinculo_sel and "__vinculo" in out.columns:
        out = out[out["__vinculo"].isin(vinculo_sel)]
    if cargo_sel and cargo_col and cargo_col in out.columns:
        out = out[out[cargo_col].astype(str).isin(cargo_sel)]
    if setor_sel and setor_col and setor_col in out.columns:
        out = out[out[setor_col].astype(str).isin(setor_sel)]
    return out


def render_sidebar_filters(
    df: pd.DataFrame,
    df_long: pd.DataFrame,
    nome_col: str | None,
    cargo_col: str | None,
    setor_col: str | None,
) -> FilterState:
    """Render sidebar and return current selected filters with full bidirectional cross-filtering."""
    with st.sidebar:
        st.header("Filtros")

        # Read active selections from session_state if available
        anos_default = sorted([str(int(a)) for a in df["__arquivo_ano"].dropna().unique().tolist()])
        cur_anos = st.session_state.get("f_anos", anos_default)
        cur_arquivo = st.session_state.get("f_arquivo", "Todos")
        cur_nome = st.session_state.get("f_nome", [])
        cur_categoria = st.session_state.get("f_categoria", [])
        cur_vinculo = st.session_state.get("f_vinculo", [])
        cur_cargo = st.session_state.get("f_cargo", [])
        cur_setor = st.session_state.get("f_setor", [])

        # 1. Anos
        df_for_anos = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            arquivo_sel_label=cur_arquivo,
            nome_sel=cur_nome,
            categoria_sel=cur_categoria,
            vinculo_sel=cur_vinculo,
            cargo_sel=cur_cargo,
            setor_sel=cur_setor,
        )
        avail_anos = sorted([str(int(a)) for a in df_for_anos["__arquivo_ano"].dropna().unique().tolist()])
        valid_cur_anos = [a for a in cur_anos if a in avail_anos] if cur_anos else avail_anos
        anos_sel = st.multiselect("Ano(s) do arquivo", options=avail_anos, default=valid_cur_anos, key="f_anos", placeholder="Selecione ano(s)")

        # 2. Busca por Arquivo
        df_for_arq = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            nome_sel=cur_nome,
            categoria_sel=cur_categoria,
            vinculo_sel=cur_vinculo,
            cargo_sel=cur_cargo,
            setor_sel=cur_setor,
        )
        arquivos_df = df_for_arq[["__arquivo", "__arquivo_label", "__arquivo_ano", "__mes_dt"]].drop_duplicates()
        arquivos_df = arquivos_df.sort_values(["__mes_dt", "__arquivo"])
        avail_arq_labels = arquivos_df["__arquivo_label"].dropna().astype(str).tolist()
        arq_options = ["Todos"] + avail_arq_labels
        idx_arq = arq_options.index(cur_arquivo) if cur_arquivo in arq_options else 0
        arquivo_sel_label = st.selectbox("Busca por Arquivo", options=arq_options, index=idx_arq, key="f_arquivo")

        # 3. Busca por Nome
        df_for_nome = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            categoria_sel=cur_categoria,
            vinculo_sel=cur_vinculo,
            cargo_sel=cur_cargo,
            setor_sel=cur_setor,
        )
        avail_nomes = sorted(df_for_nome[nome_col].dropna().astype(str).unique().tolist()) if nome_col and nome_col in df_for_nome.columns else []
        valid_cur_nome = [n for n in cur_nome if n in avail_nomes]
        nome_sel = st.multiselect("Busca por Nome", options=avail_nomes, default=valid_cur_nome, key="f_nome", placeholder="Digite para buscar nome(s)")

        # 4. Nível / Categoria do Cargo
        df_for_cat = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            nome_sel=nome_sel,
            vinculo_sel=cur_vinculo,
            cargo_sel=cur_cargo,
            setor_sel=cur_setor,
        )
        cats_in_df = df_for_cat[cargo_col].astype(str).map(get_cargo_categoria) if cargo_col and cargo_col in df_for_cat.columns else pd.Series(dtype=str)
        avail_cats = [c for c in ALL_CATEGORIAS if c in cats_in_df.unique()]
        valid_cur_cat = [c for c in cur_categoria if c in avail_cats]
        categoria_sel = st.multiselect("Nível / Categoria do Cargo", options=avail_cats, default=valid_cur_cat, key="f_categoria", placeholder="Selecione categoria(s)")

        # 5. Filtro por Vínculo
        df_for_vinc = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            nome_sel=nome_sel,
            categoria_sel=categoria_sel,
            cargo_sel=cur_cargo,
            setor_sel=cur_setor,
        )
        vincs_in_df = df_for_vinc["__vinculo"].dropna().unique().tolist() if "__vinculo" in df_for_vinc.columns else []
        avail_vincs = [v for v in ALL_VINCULOS if v in vincs_in_df]
        valid_cur_vinc = [v for v in cur_vinculo if v in avail_vincs]
        vinculo_sel = st.multiselect("Filtro por Vínculo", options=avail_vincs, default=valid_cur_vinc, key="f_vinculo", placeholder="Selecione vínculo(s)")

        # 6. Filtro por Cargo
        df_for_cargo = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            nome_sel=nome_sel,
            categoria_sel=categoria_sel,
            vinculo_sel=vinculo_sel,
            setor_sel=cur_setor,
        )
        avail_cargos = sorted(df_for_cargo[cargo_col].dropna().astype(str).unique().tolist()) if cargo_col and cargo_col in df_for_cargo.columns else []
        valid_cur_cargo = [c for c in cur_cargo if c in avail_cargos]
        cargo_sel = st.multiselect("Filtro por Cargo", options=avail_cargos, default=valid_cur_cargo, key="f_cargo", placeholder="Selecione cargo(s)")

        # 7. Filtro por Setor
        df_for_setor = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            nome_sel=nome_sel,
            categoria_sel=categoria_sel,
            vinculo_sel=vinculo_sel,
            cargo_sel=cargo_sel,
        )
        avail_setores = sorted(df_for_setor[setor_col].dropna().astype(str).unique().tolist()) if setor_col and setor_col in df_for_setor.columns else []
        valid_cur_setor = [s for s in cur_setor if s in avail_setores]
        setor_sel = st.multiselect("Filtro por Setor", options=avail_setores, default=valid_cur_setor, key="f_setor", placeholder="Selecione setor(es)")

        # 8. Busca por Tipo
        df_for_tipo = get_filtered_df(
            df,
            nome_col,
            cargo_col,
            setor_col,
            anos_sel=anos_sel,
            arquivo_sel_label=arquivo_sel_label,
            nome_sel=nome_sel,
            categoria_sel=categoria_sel,
            vinculo_sel=vinculo_sel,
            cargo_sel=cargo_sel,
            setor_sel=setor_sel,
        )
        if cargo_col and cargo_col in df_long.columns:
            id_cols_filter = [c for c in [nome_col, cargo_col, setor_col, "__vinculo", "__arquivo", "__arquivo_label", "__mes_plot", "__mes_dt", "__arquivo_ano"] if c and c in df_for_tipo.columns]
            df_long_sub = df_long.merge(df_for_tipo[id_cols_filter].drop_duplicates(), on=[c for c in id_cols_filter if c in df_long.columns], how="inner")
        else:
            df_long_sub = df_long

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

