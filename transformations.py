from __future__ import annotations

import pandas as pd

from utils import arquivo_label, clean_tipo_labels, coerce_ptbr_number


def prepare_base_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Prepare core temporal columns robustly, handling NaT safely."""
    df = df_raw.copy()
    mes_ref = df["__mes_ref"].astype("string")
    consulta = pd.to_datetime(df["__consulta_dt"], errors="coerce")
    mes_from_consulta = consulta.dt.strftime("%Y-%m")
    mes_plot = mes_ref.mask(mes_ref.isna() | mes_ref.isin(["None", "nan", "NaT", ""]), mes_from_consulta)
    df["__mes_plot"] = mes_plot
    df["__mes_dt"] = pd.to_datetime(df["__mes_plot"].astype("string") + "-01", errors="coerce")
    df["__arquivo_ano"] = df["__mes_dt"].dt.year.astype("Int64")
    df["__arquivo_label"] = pd.Series(
        [arquivo_label(arq, mes) for arq, mes in zip(df["__arquivo"].astype(str), df["__mes_ref"].astype(str), strict=False)],
        index=df.index,
    )
    return df


def build_long_dataframe(
    df: pd.DataFrame,
    id_cols: list[str],
    value_cols: list[str],
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Create long dataframe and mapping from display labels to raw columns."""
    df_long = df.melt(id_vars=id_cols, value_vars=value_cols, var_name="Tipo", value_name="Valor")
    df_long["Valor"] = coerce_ptbr_number(df_long["Valor"])
    df_long["TipoExib"] = clean_tipo_labels(df_long["Tipo"])
    df_long = df_long[df_long["TipoExib"].str.strip().ne("")]
    tipo_map = (
        df_long[["Tipo", "TipoExib"]]
        .drop_duplicates()
        .groupby("TipoExib")["Tipo"]
        .apply(lambda s: sorted(s.astype(str).unique().tolist()))
        .to_dict()
    )
    return df_long, tipo_map


def filter_long_dataframe(
    df_long: pd.DataFrame,
    anos_sel: list[str],
    arquivo_sel_label: str,
    nome_sel: list[str],
    nome_col: str | None,
    cargo_sel: list[str],
    cargo_col: str | None,
    setor_sel: list[str],
    setor_col: str | None,
    tipo_sel: list[str],
) -> pd.DataFrame:
    """Apply sidebar filters to long dataframe."""
    out = df_long
    if anos_sel:
        year_numeric = pd.to_numeric(pd.Series(anos_sel), errors="coerce").dropna().astype("Int64").tolist()
        out = out[out["__arquivo_ano"].isin(year_numeric)]
    if arquivo_sel_label != "Todos":
        out = out[out["__arquivo_label"] == arquivo_sel_label]
    if nome_sel and nome_col and nome_col in out.columns:
        out = out[out[nome_col].astype(str).isin(nome_sel)]
    if cargo_sel and cargo_col and cargo_col in out.columns:
        out = out[out[cargo_col].astype(str).isin(cargo_sel)]
    if setor_sel and setor_col and setor_col in out.columns:
        out = out[out[setor_col].astype(str).isin(setor_sel)]
    if tipo_sel:
        out = out[out["TipoExib"].isin(tipo_sel)]
    return out


def filter_detail_dataframe(
    df: pd.DataFrame,
    anos_sel: list[str],
    arquivo_sel_label: str,
    nome_sel: list[str],
    nome_col: str | None,
    cargo_sel: list[str],
    cargo_col: str | None,
    setor_sel: list[str],
    setor_col: str | None,
    tipo_sel: list[str],
    tipo_map: dict[str, list[str]],
) -> pd.DataFrame:
    """Apply filters to wide detail dataframe."""
    out = df
    if anos_sel:
        year_numeric = pd.to_numeric(pd.Series(anos_sel), errors="coerce").dropna().astype("Int64").tolist()
        out = out[out["__arquivo_ano"].isin(year_numeric)]
    if arquivo_sel_label != "Todos":
        out = out[out["__arquivo_label"] == arquivo_sel_label]
    if nome_sel and nome_col and nome_col in out.columns:
        out = out[out[nome_col].astype(str).isin(nome_sel)]
    if cargo_sel and cargo_col and cargo_col in out.columns:
        out = out[out[cargo_col].astype(str).isin(cargo_sel)]
    if setor_sel and setor_col and setor_col in out.columns:
        out = out[out[setor_col].astype(str).isin(setor_sel)]

    all_tipo_labels = sorted(tipo_map.keys())
    if tipo_sel and set(tipo_sel) != set(all_tipo_labels):
        selected_existing = sorted(set(c for t in tipo_sel for c in tipo_map.get(t, []) if c in out.columns))
        if selected_existing:
            numeric_selected = pd.DataFrame({c: coerce_ptbr_number(out[c]) for c in selected_existing}, index=out.index)
            mask_any = numeric_selected.fillna(0).ne(0).any(axis=1)
            out = out[mask_any]
    return out
