from __future__ import annotations

import numpy as np
import pandas as pd

from .schema import DEFAULT_SCHEMA, Schema


def clean_hospital_data(df: pd.DataFrame, schema: Schema = DEFAULT_SCHEMA) -> pd.DataFrame:
    out = df.copy()
    out[schema.timestamp] = pd.to_datetime(out[schema.timestamp], errors="coerce")
    out = out.dropna(subset=[schema.timestamp])
    out = out.drop_duplicates(subset=[schema.timestamp], keep="last")
    out = out.sort_values(schema.timestamp).reset_index(drop=True)

    for col in schema.numeric_columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out.loc[out[col] < 0, col] = np.nan

    out[schema.bed_occupancy] = out[schema.bed_occupancy].clip(upper=100)

    for col in schema.numeric_columns:
        out[col] = out[col].interpolate(limit=3, limit_direction="both")
        out[col] = out[col].fillna(out[col].median())
    return out


def data_quality_report(df: pd.DataFrame, schema: Schema = DEFAULT_SCHEMA) -> dict:
    ts = pd.to_datetime(df[schema.timestamp], errors="coerce")
    valid = ts.dropna().sort_values().drop_duplicates()
    gaps = int((valid.diff().dropna() > pd.Timedelta(hours=1)).sum()) if len(valid) > 1 else 0
    return {
        "rows": int(len(df)),
        "duplicate_timestamps": int(ts.duplicated().sum()),
        "invalid_timestamps": int(ts.isna().sum()),
        "start": str(valid.iloc[0]) if len(valid) else None,
        "end": str(valid.iloc[-1]) if len(valid) else None,
        "gaps_longer_than_1h": gaps,
        "missing_by_column": {c: int(df[c].isna().sum()) for c in schema.numeric_columns if c in df},
    }