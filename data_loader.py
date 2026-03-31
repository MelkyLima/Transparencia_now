from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class LoadedFile:
    path: Path
    consulta_dt: datetime | None
    df: pd.DataFrame


def try_parse_datetime_ptbr(value: str) -> datetime | None:
    value = (value or "").strip().strip('"').strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def parse_mes_ref_from_filename(name: str) -> str | None:
    stem = Path(name).stem
    m = re.search(r"(?<!\d)(\d{2})[-_](\d{2})(?!\d)", stem)
    if m:
        mm, yy = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12:
            return f"20{yy:02d}-{mm:02d}"
    m = re.search(r"(?<!\d)(\d{4})[-_](\d{2})(?!\d)", stem)
    if m:
        yyyy, mm = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12:
            return f"{yyyy:04d}-{mm:02d}"
    return None


def detect_text_encoding(path: Path, candidates: list[str]) -> str:
    data = path.read_bytes()
    for enc in candidates:
        try:
            data.decode(enc, errors="strict")
            return enc
        except UnicodeDecodeError:
            continue
    return "latin1"


def read_csv_with_fallbacks(path: Path) -> LoadedFile:
    enc_candidates = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    chosen_enc = detect_text_encoding(path, enc_candidates)

    consulta_dt: datetime | None = None
    try:
        first_line = path.read_text(encoding=chosen_enc, errors="strict").splitlines()[:1]
        if first_line:
            parts = [p.strip() for p in first_line[0].split(";") if p.strip()]
            if len(parts) >= 2:
                consulta_dt = try_parse_datetime_ptbr(parts[1].strip().strip('"'))
    except Exception:
        consulta_dt = None

    encodings = [chosen_enc] + [e for e in enc_candidates if e != chosen_enc]
    seps = [";", ","]
    last_err: Exception | None = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(
                    path,
                    sep=sep,
                    engine="python",
                    quotechar='"',
                    skiprows=1,
                    dtype=str,
                    encoding=enc,
                    encoding_errors="strict",
                )
                df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed")]
                return LoadedFile(path=path, consulta_dt=consulta_dt, df=df)
            except Exception as exc:
                last_err = exc

    try:
        df = pd.read_csv(
            path,
            engine="python",
            skiprows=1,
            dtype=str,
            encoding=chosen_enc,
            encoding_errors="replace",
        )
        df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed")]
        return LoadedFile(path=path, consulta_dt=consulta_dt, df=df)
    except Exception:
        if last_err:
            raise last_err
        raise


def list_csv_files(folder: Path, recursive: bool = False) -> list[Path]:
    if recursive:
        return sorted([p for p in folder.rglob("*.csv") if p.is_file()])
    return sorted([p for p in folder.glob("*.csv") if p.is_file()])


def load_all_dataframe(files: list[Path]) -> pd.DataFrame:
    loaded = [read_csv_with_fallbacks(p) for p in files]
    frames: list[pd.DataFrame] = []
    for item in loaded:
        df = item.df.copy()
        df["__arquivo"] = item.path.name
        df["__consulta_dt"] = item.consulta_dt
        df["__mes_ref"] = parse_mes_ref_from_filename(item.path.name)
        if df["__mes_ref"].isna().all() and item.consulta_dt:
            df["__mes_ref"] = item.consulta_dt.strftime("%Y-%m")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
