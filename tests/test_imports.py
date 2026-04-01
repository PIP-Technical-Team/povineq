"""Tests for package imports and public API surface."""

from __future__ import annotations

import povineq


def test_version_accessible():
    assert hasattr(povineq, "__version__")
    assert isinstance(povineq.__version__, str)
    assert povineq.__version__ == "0.1.0"


def test_all_public_functions_importable():
    expected = [
        "get_stats", "get_wb", "get_agg",
        "get_cp", "get_cp_ki", "unnest_ki",
        "get_aux", "display_aux", "call_aux",
        "get_countries", "get_regions", "get_cpi",
        "get_dictionary", "get_gdp", "get_incgrp_coverage",
        "get_interpolated_means", "get_hfce", "get_pop",
        "get_pop_region", "get_ppp", "get_region_coverage",
        "get_survey_means",
        "check_api", "get_versions", "get_pip_info",
        "delete_cache", "get_cache_info",
        "change_grouped_stats_to_csv",
        "PIPError", "PIPAPIError", "PIPRateLimitError",
        "PIPConnectionError", "PIPValidationError",
        "PIPResponse",
    ]
    for name in expected:
        assert hasattr(povineq, name), f"Missing public name: {name}"


def test_all_list_is_subset_of_dir():
    """Every name in __all__ should be accessible via dir(povineq)."""
    for name in povineq.__all__:
        assert hasattr(povineq, name), f"{name!r} in __all__ but not importable"


def test_exception_hierarchy():
    from povineq import PIPAPIError, PIPConnectionError, PIPError, PIPRateLimitError, PIPValidationError

    assert issubclass(PIPAPIError, PIPError)
    assert issubclass(PIPRateLimitError, PIPError)
    assert issubclass(PIPConnectionError, PIPError)
    assert issubclass(PIPValidationError, PIPError)
