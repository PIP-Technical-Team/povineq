"""Tests for _constants.py."""

from __future__ import annotations

from povineq._constants import (
    API_VERSION,
    COLUMN_RENAMES,
    DEFAULT_COUNTRY,
    DEFAULT_FORMAT,
    DEFAULT_FORMAT_AUX,
    DEFAULT_POVLINE_CP,
    DEFAULT_POVLINE_CP_2011,
    DEFAULT_PPP_VERSION,
    DEFAULT_YEAR,
    ENDPOINT_AUX,
    ENDPOINT_CP_DOWNLOAD,
    ENDPOINT_CP_KEY_INDICATORS,
    ENDPOINT_HEALTH_CHECK,
    ENDPOINT_PIP,
    ENDPOINT_PIP_GRP,
    ENDPOINT_PIP_INFO,
    ENDPOINT_VERSIONS,
    ENV_DEV_URL,
    ENV_QA_URL,
    PROD_URL,
    USER_AGENT,
)


def test_prod_url():
    assert PROD_URL == "https://api.worldbank.org/pip"


def test_api_version():
    assert API_VERSION == "v1"


def test_endpoints():
    assert ENDPOINT_PIP == "pip"
    assert ENDPOINT_PIP_GRP == "pip-grp"
    assert ENDPOINT_AUX == "aux"
    assert ENDPOINT_CP_DOWNLOAD == "cp-download"
    assert ENDPOINT_CP_KEY_INDICATORS == "cp-key-indicators"
    assert ENDPOINT_HEALTH_CHECK == "health-check"
    assert ENDPOINT_VERSIONS == "versions"
    assert ENDPOINT_PIP_INFO == "pip-info"


def test_defaults():
    assert DEFAULT_COUNTRY == "all"
    assert DEFAULT_YEAR == "all"
    assert DEFAULT_POVLINE_CP == 2.15
    assert DEFAULT_POVLINE_CP_2011 == 1.9
    assert DEFAULT_PPP_VERSION == 2017
    assert DEFAULT_FORMAT == "arrow"
    assert DEFAULT_FORMAT_AUX == "json"


def test_env_vars():
    assert ENV_QA_URL == "PIP_QA_URL"
    assert ENV_DEV_URL == "PIP_DEV_URL"


def test_user_agent_contains_package_name():
    assert "povineq" in USER_AGENT


def test_column_renames_mapping():
    assert COLUMN_RENAMES["survey_year"] == "welfare_time"
    assert COLUMN_RENAMES["reporting_year"] == "year"
    assert COLUMN_RENAMES["reporting_pop"] == "pop"
    assert COLUMN_RENAMES["reporting_gdp"] == "gdp"
    assert COLUMN_RENAMES["reporting_pce"] == "hfce"
    assert COLUMN_RENAMES["pce_data_level"] == "hfce_data_level"
    assert len(COLUMN_RENAMES) == 6
