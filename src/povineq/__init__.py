"""povineq — Python wrapper for the World Bank PIP API.

Usage::

    import povineq

    # Core statistics
    df = povineq.get_stats(country="AGO", year=2000)
    df = povineq.get_wb()
    df = povineq.get_agg(aggregate="fcv")

    # Country profiles
    df = povineq.get_cp(country="AGO")
    df = povineq.get_cp_ki(country="IDN")

    # Auxiliary tables
    tables = povineq.get_aux()
    df = povineq.get_aux("gdp")
    df = povineq.get_countries()

    # Info & cache
    status = povineq.check_api()
    info = povineq.get_pip_info()
    df_versions = povineq.get_versions()
    povineq.delete_cache()
    cache = povineq.get_cache_info()
"""

from __future__ import annotations

from povineq._cache import delete_cache, get_cache_info
from povineq._errors import (
    PIPAPIError,
    PIPConnectionError,
    PIPError,
    PIPRateLimitError,
    PIPValidationError,
)
from povineq._response import PIPResponse
from povineq.auxiliary import (
    call_aux,
    display_aux,
    get_aux,
    get_countries,
    get_cpi,
    get_dictionary,
    get_gdp,
    get_hfce,
    get_incgrp_coverage,
    get_interpolated_means,
    get_pop,
    get_pop_region,
    get_ppp,
    get_region_coverage,
    get_regions,
    get_survey_means,
)
from povineq.country_profiles import get_cp, get_cp_ki, unnest_ki
from povineq.info import check_api, get_pip_info, get_versions
from povineq.stats import get_agg, get_stats, get_wb
from povineq.utils import change_grouped_stats_to_csv

try:
    from importlib.metadata import version

    __version__ = version("povineq")
except Exception:
    __version__ = "0.1.0"  # fallback when package is not installed (e.g. editable source)

__all__ = [  # noqa: RUF022
    # Version
    "__version__",
    # Core stats
    "get_stats",
    "get_wb",
    "get_agg",
    # Country profiles
    "get_cp",
    "get_cp_ki",
    "unnest_ki",
    # Auxiliary tables
    "get_aux",
    "display_aux",
    "call_aux",
    "get_countries",
    "get_regions",
    "get_cpi",
    "get_dictionary",
    "get_gdp",
    "get_incgrp_coverage",
    "get_interpolated_means",
    "get_hfce",
    "get_pop",
    "get_pop_region",
    "get_ppp",
    "get_region_coverage",
    "get_survey_means",
    # Info
    "check_api",
    "get_versions",
    "get_pip_info",
    # Cache
    "delete_cache",
    "get_cache_info",
    # Utilities
    "change_grouped_stats_to_csv",
    # Exceptions
    "PIPError",
    "PIPAPIError",
    "PIPRateLimitError",
    "PIPConnectionError",
    "PIPValidationError",
    # Response type
    "PIPResponse",
]
