"""Tests for utility functions (utils.py)."""

from __future__ import annotations

import pandas as pd
import pytest

from povineq.utils import change_grouped_stats_to_csv, rename_cols


class TestChangeGroupedStatsToCsv:
    def test_basic_decile_unpacking(self, sample_grouped_df):
        df = change_grouped_stats_to_csv(sample_grouped_df)
        assert "deciles" not in df.columns
        for i in range(1, 11):
            assert f"decile{i}" in df.columns
        assert df["decile1"].iloc[0] == pytest.approx(0.05)
        assert df["decile10"].iloc[0] == pytest.approx(0.19)

    def test_no_deciles_column_unchanged(self):
        df = pd.DataFrame({"country": ["AGO"], "year": [2000]})
        result = change_grouped_stats_to_csv(df)
        assert list(result.columns) == ["country", "year"]

    def test_deciles_of_different_lengths(self):
        df = pd.DataFrame({
            "country": ["AGO", "ALB"],
            "deciles": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        })
        result = change_grouped_stats_to_csv(df)
        assert "decile1" in result.columns
        assert "decile3" in result.columns
        assert result["decile1"].iloc[1] == pytest.approx(0.4)

    def test_none_deciles_handled(self):
        df = pd.DataFrame({
            "country": ["AGO"],
            "deciles": [None],
        })
        # No deciles to expand → should drop deciles column gracefully
        result = change_grouped_stats_to_csv(df)
        assert "deciles" not in result.columns

    def test_preserves_other_columns(self, sample_grouped_df):
        result = change_grouped_stats_to_csv(sample_grouped_df)
        assert "country_code" in result.columns
        assert "year" in result.columns


class TestRenameCols:
    def test_basic_rename(self):
        df = pd.DataFrame({"old_name": [1, 2]})
        result = rename_cols(df, ["old_name"], ["new_name"])
        assert "new_name" in result.columns
        assert "old_name" not in result.columns

    def test_partial_rename_when_col_missing(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        # "c" doesn't exist — should not raise
        result = rename_cols(df, ["a", "c"], ["x", "y"])
        assert "x" in result.columns
        assert "b" in result.columns  # unchanged
        assert "c" not in result.columns

    def test_mismatched_lengths_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError):
            rename_cols(df, ["a"], ["x", "y"])

    def test_column_rename_mapping(self):
        """Apply the real COLUMN_RENAMES mapping from constants."""
        from povineq._constants import COLUMN_RENAMES

        df = pd.DataFrame({
            "survey_year": [2000],
            "reporting_year": [2000],
            "reporting_pop": [1e6],
            "reporting_gdp": [5e9],
            "reporting_pce": [3e9],
            "pce_data_level": ["national"],
        })
        result = rename_cols(df, list(COLUMN_RENAMES.keys()), list(COLUMN_RENAMES.values()))
        assert "welfare_time" in result.columns
        assert "year" in result.columns
        assert "pop" in result.columns
        assert "gdp" in result.columns
        assert "hfce" in result.columns
        assert "hfce_data_level" in result.columns
