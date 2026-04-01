"""Shared pytest fixtures and configuration for povineq tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Online / offline markers
# ---------------------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "online: requires internet connectivity")
    config.addinivalue_line("markers", "slow: slow tests")


# ---------------------------------------------------------------------------
# Arrow fixture helpers
# ---------------------------------------------------------------------------

def _make_arrow_bytes(records: list[dict]) -> bytes:
    """Build minimal Arrow IPC (Feather v2) bytes from a list of dicts."""
    table = pa.Table.from_pydict(
        {k: [r[k] for r in records] for k in records[0]}
    )
    buf = io.BytesIO()
    writer = ipc.new_file(buf, table.schema)
    writer.write_table(table)
    writer.close()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures: raw response bytes
# ---------------------------------------------------------------------------

@pytest.fixture()
def stats_arrow_bytes() -> bytes:
    """Minimal Arrow response for a single country-year get_stats query."""
    return _make_arrow_bytes([
        {
            "country_code": "AGO",
            "reporting_year": 2000,
            "reporting_level": "national",
            "welfare_type": "consumption",
            "headcount": 0.544,
            "poverty_gap": 0.218,
            "estimate_type": "survey",
        }
    ])


@pytest.fixture()
def stats_json_bytes() -> bytes:
    """Minimal JSON response for get_stats (list of dicts)."""
    data = [
        {
            "country_code": "AGO",
            "reporting_year": 2000,
            "reporting_level": "national",
            "welfare_type": "consumption",
            "headcount": 0.544,
            "poverty_gap": 0.218,
            "estimate_type": "survey",
        }
    ]
    return json.dumps(data).encode()


@pytest.fixture()
def stats_csv_bytes() -> bytes:
    """Minimal CSV response for get_stats."""
    return (
        b"country_code,reporting_year,reporting_level,welfare_type,headcount,poverty_gap,estimate_type\n"
        b"AGO,2000,national,consumption,0.544,0.218,survey\n"
    )


@pytest.fixture()
def aux_json_bytes() -> bytes:
    """Minimal JSON response for get_aux() with no table (returns table list)."""
    data = {"tables": ["countries", "regions", "cpi", "gdp", "ppp"]}
    return json.dumps(data).encode()


@pytest.fixture()
def gdp_json_bytes() -> bytes:
    """Minimal JSON response for get_aux('gdp')."""
    data = [
        {"country_code": "AGO", "year": 2000, "gdp": 3000.0},
        {"country_code": "AGO", "year": 2001, "gdp": 3100.0},
    ]
    return json.dumps(data).encode()


@pytest.fixture()
def error_404_bytes() -> bytes:
    """Minimal 404 error body from the PIP API."""
    data = {
        "error": ["Resource not found"],
        "details": {
            "country": {
                "msg": ["The country code 'XYZ' is not valid."],
                "valid": ["AGO", "ALB", "ARG"],
            }
        },
    }
    return json.dumps(data).encode()


@pytest.fixture()
def rate_limit_bytes() -> bytes:
    """Minimal 429 rate-limit response body."""
    data = {"message": "Rate limit is exceeded. Try again in 5 seconds."}
    return json.dumps(data).encode()


# ---------------------------------------------------------------------------
# Fixtures: parsed DataFrames
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_stats_df() -> pd.DataFrame:
    """Simple one-row stats DataFrame."""
    return pd.DataFrame({
        "country_code": ["AGO"],
        "year": [2000],
        "reporting_level": ["national"],
        "welfare_type": ["consumption"],
        "headcount": [0.544],
        "poverty_gap": [0.218],
        "estimate_type": ["survey"],
    })


@pytest.fixture()
def sample_grouped_df() -> pd.DataFrame:
    """DataFrame with a 'deciles' list-column for testing pivoting."""
    return pd.DataFrame({
        "country_code": ["AGO"],
        "year": [2000],
        "deciles": [[0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.19]],
    })
