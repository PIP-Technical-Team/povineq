"""Tests for the in-memory auxiliary table store (_aux_store.py)."""

from __future__ import annotations

import pandas as pd
import pytest

from povineq._aux_store import _store, call_aux, set_aux


@pytest.fixture(autouse=True)
def clear_store():
    """Reset the global store before each test."""
    _store.clear()
    yield
    _store.clear()


class TestSetAux:
    def test_basic_store(self):
        df = pd.DataFrame({"a": [1, 2]})
        result = set_aux("test_table", df)
        assert result is True
        assert "test_table" in _store

    def test_replace_false_raises(self):
        df = pd.DataFrame({"a": [1]})
        set_aux("t", df)
        with pytest.raises(ValueError, match="already exists"):
            set_aux("t", df, replace=False)

    def test_replace_true_overwrites(self):
        df1 = pd.DataFrame({"a": [1]})
        df2 = pd.DataFrame({"a": [99]})
        set_aux("t", df1)
        set_aux("t", df2, replace=True)
        result = call_aux("t")
        assert result["a"].iloc[0] == 99

    def test_stores_correct_data(self):
        df = pd.DataFrame({"country": ["AGO"], "year": [2000]})
        set_aux("my_table", df)
        retrieved = call_aux("my_table")
        pd.testing.assert_frame_equal(retrieved, df)


class TestCallAux:
    def test_list_all_when_none(self):
        df1 = pd.DataFrame({"x": [1]})
        df2 = pd.DataFrame({"y": [2]})
        set_aux("t1", df1)
        set_aux("t2", df2)
        names = call_aux(None)
        assert isinstance(names, list)
        assert "t1" in names
        assert "t2" in names

    def test_empty_store_returns_empty_list(self):
        result = call_aux(None)
        assert result == []

    def test_missing_table_raises_key_error(self):
        with pytest.raises(KeyError, match="missing_table"):
            call_aux("missing_table")

    def test_retrieve_stored_table(self):
        df = pd.DataFrame({"a": [10, 20]})
        set_aux("gdp", df)
        result = call_aux("gdp")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
