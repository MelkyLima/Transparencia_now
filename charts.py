from __future__ import annotations

import pandas as pd
import plotly.express as px

from utils import format_brl, mes_label_curto, mes_label_longo


RE_TOTAL_CREDITOS = r"total de cr[ée]ditos"
RE_TOTAL_DEBITOS = r"total de d[ée]bitos"
RE_REND_LIQ = r"rendimento l[íi]quido"
RE_DEBITO_PARTES = r"imposto|previd|desconto|teto"
RE_EXCLUI_CREDITO = r"total de cr[ée]ditos|total de d[ée]bitos|rendimento l[íi]quido|imposto|previd|desconto|teto"


def build_totais_tipo(df_long_filtered: pd.DataFrame) -> pd.DataFrame:
    totais = (
        df_long_filtered.groupby("TipoExib", dropna=False)["Valor"]
        .sum(min_count=1)
        .fillna(0)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"TipoExib": "Tipo"})
    )
    totais = totais[totais["Tipo"].astype(str).str.strip().ne("")]
    totais["Total"] = totais["Valor"].map(format_brl)
    return totais


def build_indenizacao_stats(df_long_filtered: pd.DataFrame, totais_tipo: pd.DataFrame) -> dict[str, str]:
    inden_total = float(
        totais_tipo.loc[totais_tipo["Tipo"].astype(str).str.contains("indeniza", case=False, na=False, regex=False), "Valor"].sum()
    )
    inden_df = df_long_filtered[df_long_filtered["TipoExib"].str.contains("indeniza", case=False, na=False, regex=False)].dropna(
        subset=["__mes_dt"]
    )
    if inden_df.empty:
        return {
            "mes_label": "-",
            "meses_3m_label": "-",
            "ano_recente": "-",
            "ano_anterior": "-",
            "total_mes_atual": format_brl(0),
            "total_3m": format_brl(0),
            "total_ultimo_ano": format_brl(0),
            "total_ano_anterior": format_brl(0),
            "inden_total": format_brl(inden_total),
        }

    mes_atual = inden_df["__mes_dt"].max()
    ini_3m = mes_atual - pd.DateOffset(months=2)
    total_mes_atual = float(inden_df.loc[inden_df["__mes_dt"] == mes_atual, "Valor"].sum())
    ultimos_3m_df = inden_df.loc[inden_df["__mes_dt"].between(ini_3m, mes_atual)]
    total_3m = float(ultimos_3m_df["Valor"].sum())
    meses_3m = sorted(ultimos_3m_df["__mes_dt"].dropna().unique().tolist())
    meses_3m_label = ", ".join([mes_label_curto(pd.Timestamp(m)) for m in meses_3m]) if meses_3m else "-"
    ano_recente = int(mes_atual.year)
    ano_anterior = ano_recente - 1
    total_ultimo_ano = float(inden_df.loc[inden_df["__mes_dt"].dt.year == ano_recente, "Valor"].sum())
    total_ano_anterior = float(inden_df.loc[inden_df["__mes_dt"].dt.year == ano_anterior, "Valor"].sum())

    return {
        "mes_label": mes_label_longo(pd.Timestamp(mes_atual)),
        "meses_3m_label": meses_3m_label,
        "ano_recente": str(ano_recente),
        "ano_anterior": str(ano_anterior),
        "total_mes_atual": format_brl(total_mes_atual),
        "total_3m": format_brl(total_3m),
        "total_ultimo_ano": format_brl(total_ultimo_ano),
        "total_ano_anterior": format_brl(total_ano_anterior),
        "inden_total": format_brl(inden_total),
    }


def _pick_total(df_totais: pd.DataFrame, regex_key: str) -> float:
    mask = df_totais["Tipo"].astype(str).str.contains(regex_key, case=False, na=False, regex=True)
    if not mask.any():
        return 0.0
    return float(df_totais.loc[mask, "Valor"].sum())


def _compress_pizza_slices(df_pizza: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    d = df_pizza.sort_values("Valor", ascending=False).reset_index(drop=True)
    if len(d) <= top_n:
        return d
    head = d.head(top_n).copy()
    other_sum = float(d.iloc[top_n:]["Valor"].sum())
    if other_sum > 0:
        head.loc[len(head)] = {"Tipo": "Outros", "Valor": other_sum}
    return head


def build_pizza_creditos(totais_tipo: pd.DataFrame) -> pd.DataFrame:
    total_creditos = _pick_total(totais_tipo, RE_TOTAL_CREDITOS)
    mask_credito_comp = ~totais_tipo["Tipo"].astype(str).str.contains(RE_EXCLUI_CREDITO, case=False, na=False, regex=True)
    comp = totais_tipo.loc[mask_credito_comp, ["Tipo", "Valor"]].copy()
    comp["Valor"] = pd.to_numeric(comp["Valor"], errors="coerce").fillna(0.0)
    comp = comp[comp["Valor"] > 0]
    outros = total_creditos - float(comp["Valor"].sum())
    if outros > 0.005:
        comp.loc[len(comp)] = {"Tipo": "Outros créditos", "Valor": outros}
    if comp.empty and total_creditos > 0:
        comp = pd.DataFrame([{"Tipo": "Total de Créditos", "Valor": total_creditos}])
    return _compress_pizza_slices(comp, top_n=8)


def build_pizza_debitos(totais_tipo: pd.DataFrame) -> pd.DataFrame:
    total_debitos = _pick_total(totais_tipo, RE_TOTAL_DEBITOS)
    mask_debito_comp = totais_tipo["Tipo"].astype(str).str.contains(RE_DEBITO_PARTES, case=False, na=False, regex=True)
    comp = totais_tipo.loc[mask_debito_comp, ["Tipo", "Valor"]].copy()
    comp["Valor"] = pd.to_numeric(comp["Valor"], errors="coerce").fillna(0.0)
    comp = comp[comp["Valor"] > 0]
    outros = total_debitos - float(comp["Valor"].sum())
    if outros > 0.005:
        comp.loc[len(comp)] = {"Tipo": "Outros débitos", "Valor": outros}
    if comp.empty and total_debitos > 0:
        comp = pd.DataFrame([{"Tipo": "Total de Débitos", "Valor": total_debitos}])
    return _compress_pizza_slices(comp, top_n=8)


def build_pie_figure(df_pizza: pd.DataFrame, title: str):
    if df_pizza.empty:
        return None
    d = df_pizza.copy()
    d["ValorFormatado"] = d["Valor"].map(format_brl)
    fig = px.pie(
        d,
        names="Tipo",
        values="Valor",
        hole=0.35,
        custom_data=["ValorFormatado"],
        template="plotly_white",
        title=title,
    )
    fig.update_traces(hovertemplate="%{label}<br>%{customdata[0]}<extra></extra>", textinfo="percent")
    fig.update_layout(
        height=520,
        legend=dict(orientation="v", y=0.5, x=1.03, traceorder="normal"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def build_evolucao_dataframe(df_long_filtered: pd.DataFrame, granularidade: str = "mes") -> tuple[pd.DataFrame, list[str]]:
    """Build evolution dataframe for monthly or yearly view."""
    if granularidade == "ano":
        base = df_long_filtered.copy()
        base = base.dropna(subset=["__mes_dt"])
        if base.empty:
            return base, []
        base["AnoLabel"] = base["__mes_dt"].dt.year.astype(str)
        evol = (
            base.groupby(["AnoLabel", "TipoExib"], dropna=False)["Valor"]
            .sum(min_count=1)
            .fillna(0)
            .reset_index()
            .sort_values("AnoLabel")
        )
        tipo_ordem = (
            evol.groupby("TipoExib", dropna=False)["Valor"]
            .sum(min_count=1)
            .fillna(0)
            .sort_values(ascending=False)
            .index.tolist()
        )
        evol["TipoExib"] = pd.Categorical(evol["TipoExib"], categories=tipo_ordem, ordered=True)
        evol = evol.sort_values(["TipoExib", "AnoLabel"])
        return evol, tipo_ordem

    evol = (
        df_long_filtered.groupby(["__mes_dt", "TipoExib"], dropna=False)["Valor"]
        .sum(min_count=1)
        .fillna(0)
        .reset_index()
        .sort_values("__mes_dt")
    )
    if evol.empty:
        return evol, []
    tipo_ordem = (
        evol.groupby("TipoExib", dropna=False)["Valor"]
        .sum(min_count=1)
        .fillna(0)
        .sort_values(ascending=False)
        .index.tolist()
    )
    evol = evol.dropna(subset=["__mes_dt"]).copy()
    if evol.empty:
        return evol, tipo_ordem
    all_months = pd.date_range(evol["__mes_dt"].min(), evol["__mes_dt"].max(), freq="MS")
    idx = pd.MultiIndex.from_product([all_months, tipo_ordem], names=["__mes_dt", "TipoExib"])
    evol = evol.set_index(["__mes_dt", "TipoExib"])["Valor"].reindex(idx, fill_value=0).reset_index()
    evol["TipoExib"] = pd.Categorical(evol["TipoExib"], categories=tipo_ordem, ordered=True)
    evol["MesLabel"] = evol["__mes_dt"].dt.strftime("%m/%y")
    evol = evol.sort_values(["TipoExib", "__mes_dt"])
    return evol, tipo_ordem


def build_evolucao_figure(evol: pd.DataFrame, tipo_ordem: list[str], granularidade: str = "mes"):
    if evol.empty:
        return None
    eixo_x = "MesLabel" if granularidade == "mes" else "AnoLabel"
    eixo_label = "Mês - Ano" if granularidade == "mes" else "Ano"
    fig = px.line(
        evol,
        x=eixo_x,
        y="Valor",
        color="TipoExib",
        markers=True,
        category_orders={"TipoExib": tipo_ordem},
        template="plotly_white",
    )
    fig.update_layout(xaxis_title=eixo_label, yaxis_title="Valor (R$)", yaxis_tickprefix="R$ ", margin=dict(l=20, r=20, t=20, b=20))
    return fig
