from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def format_brl(value: float | int | None) -> str:
    """Format numeric values as Brazilian currency."""
    if value is None or pd.isna(value):
        return "R$ 0,00"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def coerce_ptbr_number(series: pd.Series) -> pd.Series:
    """Convert strings like 1.234,56 to float."""
    s = series.astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False)
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def arquivo_label(nome_arquivo: str, mes_ref: str | None) -> str:
    """Return friendly label (e.g., Marco/2025) from file metadata."""
    meses_pt = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Marco",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    if mes_ref and isinstance(mes_ref, str) and re.match(r"^\d{4}-\d{2}$", mes_ref):
        ano = int(mes_ref[:4])
        mes = int(mes_ref[5:7])
        if 1 <= mes <= 12:
            return f"{meses_pt[mes]}/{ano}"
    return Path(nome_arquivo).stem


def mes_label_curto(dt: pd.Timestamp) -> str:
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return f"{meses[int(dt.month) - 1]}/{str(int(dt.year))[-2:]}"


def mes_label_longo(dt: pd.Timestamp) -> str:
    meses = [
        "Janeiro",
        "Fevereiro",
        "Marco",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    return f"{meses[int(dt.month) - 1]}/{str(int(dt.year))[-2:]}"


def clean_tipo_labels(series: pd.Series) -> pd.Series:
    """Remove trailing numeric suffix like '(12)' from labels."""
    return series.astype(str).str.strip().str.replace(r"\s*\(\d+\)\s*$", "", regex=True)


def clean_tipo_label(text: str) -> str:
    """Scalar version of clean_tipo_labels."""
    return re.sub(r"\s*\(\d+\)\s*$", "", str(text or "").strip())


def pick_col(df: pd.DataFrame, keywords: list[str]) -> str | None:
    """
    Pick a column by priority:
    1) exact match
    2) startswith
    3) contains
    """
    cols = [c for c in df.columns if not str(c).startswith("__")]
    if not cols:
        return None

    cols_lower = {c: str(c).strip().lower() for c in cols}
    for kw in keywords:
        k = kw.strip().lower()
        for c, c_low in cols_lower.items():
            if c_low == k:
                return c
        for c, c_low in cols_lower.items():
            if c_low.startswith(k):
                return c
        for c, c_low in cols_lower.items():
            if k in c_low:
                return c
    return None
