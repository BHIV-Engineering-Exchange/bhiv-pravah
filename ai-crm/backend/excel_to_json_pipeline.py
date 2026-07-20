"""
Unified Excel → JSON ingestion helpers for ERP-like data.

Supports two input patterns under ./data/:
- A single multi-sheet workbook with sheets: Orders, Returns, Inventory
- Three separate files: orders.xlsx, returns.xlsx, inventory.xlsx

On load, data frames are:
- Column-normalized to snake_case
- Date-like columns parsed to datetime
- Filtered to relevant columns when available
- Converted to JSON-serializable list-of-dicts (NaN -> None, datetimes -> ISO)
"""

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

# Data directory is fixed for this iteration; later we can make this configurable.
DATA_DIR = Path(__file__).resolve().parent / "data"
MULTI_SHEET_CANDIDATES: Iterable[str] = ("erp_data.xlsx", "data.xlsx")


def _snake_case_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column headers to snake_case."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.lower()
        .str.strip("_")
    )
    return df


def _parse_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parse any column containing 'date' into pandas datetime (coercing failures)."""
    df = df.copy()
    date_like = [col for col in df.columns if "date" in col]
    for col in date_like:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _finalize_df(df: pd.DataFrame, relevant_cols: Optional[List[str]]) -> List[Dict]:
    """Apply normalization, trimming, and JSON-safe conversion."""
    df = _snake_case_columns(df)
    df = _parse_date_columns(df)

    if relevant_cols:
        keep = [col for col in df.columns if col in relevant_cols]
        if keep:
            df = df[keep]

    # Replace pandas NaN/NaT with None for JSON serializability.
    df = df.where(pd.notnull(df), None)

    # Convert datetime columns to ISO 8601 strings.
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns
    for col in datetime_cols:
        df[col] = df[col].apply(
            lambda val: val.isoformat().replace("+00:00", "Z") if val is not None else None
        )

    return df.to_dict(orient="records")


def _read_from_workbook(sheet_name: str) -> Optional[pd.DataFrame]:
    """
    Attempt to read a sheet from known multi-sheet workbooks.
    Returns a dataframe on success, or None if not found/available.
    """
    for candidate in MULTI_SHEET_CANDIDATES:
        workbook_path = DATA_DIR / candidate
        if not workbook_path.exists():
            continue
        try:
            return pd.read_excel(workbook_path, sheet_name=sheet_name)
        except ValueError:
            # Sheet missing; try next candidate.
            continue
    return None


def _read_source(sheet_name: str, fallback_filename: str, relevant_cols: Optional[List[str]]) -> List[Dict]:
    """
    Read from a multi-sheet workbook if possible; otherwise fall back to an individual file.
    """
    df = _read_from_workbook(sheet_name)
    if df is None:
        path = DATA_DIR / fallback_filename
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        df = pd.read_excel(path)

    return _finalize_df(df, relevant_cols)


def load_orders() -> List[Dict]:
    """Load and normalize Orders data."""
    relevant = [
        "order_id",
        "product_id",
        "quantity",
        "status",
        "order_date",
        "ship_date",
        "customer_id",
    ]
    return _read_source("Orders", "orders.xlsx", relevant)


def load_returns() -> List[Dict]:
    """Load and normalize Returns data."""
    relevant = [
        "return_id",
        "order_id",
        "product_id",
        "quantity",
        "reason",
        "status",
        "return_date",
    ]
    return _read_source("Returns", "returns.xlsx", relevant)


def load_inventory() -> List[Dict]:
    """Load and normalize Inventory data."""
    relevant = [
        "product_id",
        "sku",
        "location",
        "quantity",
        "status",
        "last_update",
        "reorder_point",
    ]
    return _read_source("Inventory", "inventory.xlsx", relevant)


def load_all() -> Dict[str, List[Dict]]:
    """Convenience wrapper to load all datasets at once."""
    return {
        "orders": load_orders(),
        "returns": load_returns(),
        "inventory": load_inventory(),
    }
