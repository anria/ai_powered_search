# pages/data_loader.py
"""
Central data loader for the product catalogue.

The CSV is read ONCE per Python process and cached in a module-level
DataFrame. Every view imports `PRODUCTS_DF` (or calls `get_products()`)
and gets the same object — no repeated file I/O, no repeated parsing.
"""

import os
import threading
from pathlib import Path

import pandas as pd
from django.conf import settings


# Resolve the CSV path from settings, falling back to /data/product.csv
CSV_PATH = 'data/product.csv'
# PRODUCTS_DF = pd.read_csv('data/product.csv', sep='\t') 

_lock = threading.Lock()
_df = None   # module-level cache


def _load_csv(path) -> pd.DataFrame:
    """Read the CSV into a DataFrame, coercing everything to string for easy search."""
    #if not path.exists():
    #    print(f"[data_loader] CSV not found: {path}")
    #    return pd.DataFrame()

    try:
        df = pd.read_csv(path, sep='\t')
        print(f"[data_loader] Loaded {len(df):,} rows from {path}")
        return df
    except Exception as e:
        print(f"[data_loader] Failed to read {path}: {e}")
        return pd.DataFrame()


def get_products() -> pd.DataFrame:
    """
    Return the cached product DataFrame, loading it on first call.

    Thread-safe: if two requests race on the very first hit, only one
    thread performs the actual read.
    """
    global _df
    if _df is None:
        with _lock:
            if _df is None:            # double-checked locking
                _df = _load_csv(CSV_PATH)
    return _df


def reload_products() -> pd.DataFrame:
    """Force a re-read of the CSV (useful for a dev-only refresh endpoint)."""
    global _df
    with _lock:
        _df = _load_csv(CSV_PATH)
    return _df