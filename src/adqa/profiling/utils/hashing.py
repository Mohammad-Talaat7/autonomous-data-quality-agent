from __future__ import annotations

import hashlib

import pandas as pd


def hash_dataframe(df: pd.DataFrame, fast: bool = True, sample_rows: int = 1000) -> str:
    """
    Deterministic hash for caching.

    If fast=True:
    - Hashes column names & dtypes (schema)
    - Hashes df.shape
    - Hashes a sample (first and last N rows)

    If fast=False:
    - Hashes entire content (Slow for large DFs)
    """
    hasher = hashlib.sha256()

    # 1. Include schema (column names and order + dtypes)
    schema_info = f"{list(df.columns)}:{list(df.dtypes)}"
    hasher.update(schema_info.encode("utf-8"))

    # 2. Include shape
    hasher.update(str(df.shape).encode("utf-8"))

    if fast:
        # 3. Fast Sampling: First N and Last N rows
        if len(df) <= sample_rows * 2:
            content_to_hash = df
        else:
            content_to_hash = pd.concat([df.head(sample_rows), df.tail(sample_rows)])

        # Hash the sampled content
        sample_hash = pd.util.hash_pandas_object(content_to_hash, index=True).to_numpy()
        hasher.update(sample_hash.tobytes())
    else:
        # 4. Strict Hashing: Entire content
        full_content_hash = pd.util.hash_pandas_object(df, index=True).to_numpy()
        hasher.update(full_content_hash.tobytes())

    return hasher.hexdigest()
