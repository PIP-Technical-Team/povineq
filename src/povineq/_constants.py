"""Constants for the povineq package — base URLs, endpoints, and defaults."""

# API
PROD_URL: str = "https://api.worldbank.org/pip"
USER_AGENT: str = "povineq (https://github.com/PIP-Technical-Team/povineq)"
API_VERSION: str = "v1"

# Endpoints
ENDPOINT_PIP: str = "pip"
ENDPOINT_PIP_GRP: str = "pip-grp"
ENDPOINT_AUX: str = "aux"
ENDPOINT_CP_DOWNLOAD: str = "cp-download"
ENDPOINT_CP_KEY_INDICATORS: str = "cp-key-indicators"
ENDPOINT_HEALTH_CHECK: str = "health-check"
ENDPOINT_VERSIONS: str = "versions"
ENDPOINT_PIP_INFO: str = "pip-info"

# Server environment variable names
ENV_QA_URL: str = "PIP_QA_URL"
ENV_DEV_URL: str = "PIP_DEV_URL"

# Default parameter values
DEFAULT_COUNTRY: str = "all"
DEFAULT_YEAR: str = "all"
DEFAULT_POVLINE_CP: float = 2.15
DEFAULT_POVLINE_CP_2011: float = 1.9
DEFAULT_PPP_VERSION: int = 2017
DEFAULT_FORMAT: str = "arrow"
DEFAULT_FORMAT_AUX: str = "json"  # aux endpoint does not support arrow

# Column rename mapping.
# The PIP API returns columns under names that differ from the pipr R package
# convention used throughout this library.  These renames are applied by
# ``parse_response()`` to every response so downstream code can use the same
# field names regardless of whether it calls this package or pipr.
# Background: https://github.com/PIP-Technical-Team/pipapi/issues/207
# Keys are raw API column names; values are the pipr-compatible output names.
COLUMN_RENAMES: dict[str, str] = {
    "survey_year": "welfare_time",
    "reporting_year": "year",
    "reporting_pop": "pop",
    "reporting_gdp": "gdp",
    "reporting_pce": "hfce",
    "pce_data_level": "hfce_data_level",
}
