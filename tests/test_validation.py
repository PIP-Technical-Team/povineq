"""Tests for _validation.py — pydantic parameter models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from povineq._validation import AggParams, AuxParams, CpKiParams, CpParams, StatsParams


# ---------------------------------------------------------------------------
# StatsParams
# ---------------------------------------------------------------------------

class TestStatsParams:

    def test_defaults(self):
        p = StatsParams()
        assert p.country == "all"
        assert p.year == "all"
        assert p.povline is None
        assert p.popshare is None
        assert p.fill_gaps is False
        assert p.nowcast is False
        assert p.subgroup is None
        assert p.welfare_type == "all"
        assert p.reporting_level == "all"
        assert p.format == "arrow"

    def test_popshare_nullifies_povline(self):
        p = StatsParams(povline=1.9, popshare=0.4)
        assert p.popshare == 0.4
        assert p.povline is None

    def test_nowcast_implies_fill_gaps(self):
        p = StatsParams(nowcast=True)
        assert p.fill_gaps is True
        assert p.nowcast is True

    def test_fill_gaps_false_forces_nowcast_false(self):
        p = StatsParams(fill_gaps=False, nowcast=False)
        assert p.nowcast is False

    def test_subgroup_clears_fill_gaps_and_nowcast(self):
        p = StatsParams(subgroup="wb_regions", fill_gaps=True, nowcast=True)
        assert p.subgroup == "wb_regions"
        # fill_gaps and nowcast are cleared when subgroup is set
        assert p.fill_gaps is None
        assert p.nowcast is None

    def test_subgroup_none_valid(self):
        p = StatsParams(subgroup="none")
        assert p.subgroup == "none"

    def test_subgroup_invalid_raises(self):
        with pytest.raises(ValidationError):
            StatsParams(subgroup="invalid_subgroup")

    def test_country_list(self):
        p = StatsParams(country=["AGO", "ALB"])
        assert p.country == ["AGO", "ALB"]

    def test_year_list(self):
        p = StatsParams(year=[2000, 2001])
        assert p.year == [2000, 2001]

    def test_to_query_params_drops_none(self):
        p = StatsParams(country="AGO", year=2000)
        q = p.to_query_params()
        # povline is None — should not appear
        assert "povline" not in q
        assert q["country"] == "AGO"
        assert q["year"] == "2000"

    def test_to_query_params_list_to_csv(self):
        p = StatsParams(country=["AGO", "ALB"], year=[2000, 2001])
        q = p.to_query_params()
        assert q["country"] == "AGO,ALB"
        assert q["year"] == "2000,2001"

    def test_to_query_params_bool_lowercase(self):
        p = StatsParams(fill_gaps=True)
        q = p.to_query_params()
        assert q["fill_gaps"] == "true"

    def test_format_options(self):
        for fmt in ("arrow", "json", "csv"):
            p = StatsParams(format=fmt)
            assert p.format == fmt

    def test_format_invalid(self):
        with pytest.raises(ValidationError):
            StatsParams(format="rds")


# ---------------------------------------------------------------------------
# CpParams
# ---------------------------------------------------------------------------

class TestCpParams:

    def test_defaults(self):
        p = CpParams()
        assert p.country == "all"
        assert p.povline == 2.15
        assert p.ppp_version == 2017

    def test_ppp_version_2011_sets_povline_1_9_when_none(self):
        p = CpParams(povline=None, ppp_version=2011)
        assert p.povline == 1.9

    def test_explicit_povline_not_overridden(self):
        p = CpParams(povline=3.65, ppp_version=2011)
        assert p.povline == 3.65

    def test_ppp_version_2017_no_change(self):
        p = CpParams(povline=None, ppp_version=2017)
        assert p.povline is None


# ---------------------------------------------------------------------------
# CpKiParams
# ---------------------------------------------------------------------------

class TestCpKiParams:

    def test_country_required(self):
        with pytest.raises(ValidationError):
            CpKiParams()  # missing country

    def test_country_empty_string_raises(self):
        with pytest.raises(ValidationError):
            CpKiParams(country="")

    def test_valid_country(self):
        p = CpKiParams(country="IDN")
        assert p.country == "IDN"

    def test_ppp_version_2011_sets_povline_default(self):
        p = CpKiParams(country="IDN", povline=None, ppp_version=2011)
        assert p.povline == 1.9


# ---------------------------------------------------------------------------
# AuxParams
# ---------------------------------------------------------------------------

class TestAuxParams:

    def test_defaults(self):
        p = AuxParams()
        assert p.table is None
        assert p.format == "json"

    def test_table_set(self):
        p = AuxParams(table="gdp")
        assert p.table == "gdp"

    def test_format_options(self):
        for fmt in ("json", "csv"):
            p = AuxParams(format=fmt)
            assert p.format == fmt

    def test_arrow_format_invalid(self):
        with pytest.raises(ValidationError):
            AuxParams(format="arrow")

    def test_to_query_params_with_table(self):
        p = AuxParams(table="gdp", format="json")
        q = p.to_query_params()
        assert q["table"] == "gdp"
        assert q["format"] == "json"
        assert "ppp_version" not in q  # None dropped


# ---------------------------------------------------------------------------
# AggParams
# ---------------------------------------------------------------------------

class TestAggParams:

    def test_defaults(self):
        p = AggParams()
        assert p.year == "all"
        assert p.format == "json"
        assert p.aggregate is None

    def test_aggregate_set(self):
        p = AggParams(aggregate="fcv")
        assert p.aggregate == "fcv"

    def test_to_query_params_aggregate(self):
        p = AggParams(aggregate="fcv")
        q = p.to_query_params()
        assert q["aggregate"] == "fcv"


# ---------------------------------------------------------------------------
# P2.18 — boundary value and edge-case tests
# ---------------------------------------------------------------------------

class TestStatsParamsBoundary:

    @pytest.mark.parametrize("subgroup", ["WB_REGIONS", "Wb_Regions", "wb_region"])
    def test_invalid_subgroup_case_variants(self, subgroup):
        """Only exact lowercase 'wb_regions' or 'none' are valid."""
        with pytest.raises(ValidationError):
            StatsParams(subgroup=subgroup)

    def test_subgroup_with_povline_clears_fill_gaps(self):
        """subgroup should clear fill_gaps and nowcast regardless of other params."""
        p = StatsParams(subgroup="wb_regions", povline=2.15, fill_gaps=True)
        assert p.fill_gaps is None
        assert p.nowcast is None

    def test_year_list_with_duplicates_preserved(self):
        """Year duplicates are not deduped — user is responsible."""
        p = StatsParams(year=[2000, 2000, 2001])
        q = p.to_query_params()
        assert q["year"] == "2000,2000,2001"

    def test_format_csv_valid(self):
        p = StatsParams(format="csv")
        assert p.format == "csv"

    def test_api_version_only_v1_allowed(self):
        with pytest.raises(ValidationError):
            StatsParams(api_version="v2")
