"""Pydantic parameter models for PIP API endpoint validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

from povineq._constants import (
    DEFAULT_COUNTRY,
    DEFAULT_FORMAT,
    DEFAULT_FORMAT_AUX,
    DEFAULT_POVLINE_CP,
    DEFAULT_POVLINE_CP_2011,
    DEFAULT_PPP_VERSION,
    DEFAULT_YEAR,
)


class _BaseParams(BaseModel):
    """Shared helpers used across all parameter models."""

    model_config = {"arbitrary_types_allowed": True}

    def to_query_params(self) -> dict[str, str]:
        """Serialize model to a flat dict of query-string key/value pairs.

        - List values are joined with commas.
        - ``None`` values are dropped.
        - Booleans are lowercased strings (``"true"``/``"false"``).
        """
        result: dict[str, str] = {}
        for field_name, value in self.model_dump().items():
            if value is None:
                continue
            if isinstance(value, list):
                result[field_name] = ",".join(str(v) for v in value)
            elif isinstance(value, bool):
                result[field_name] = str(value).lower()
            else:
                result[field_name] = str(value)
        return result


class StatsParams(_BaseParams):
    """Parameters for :func:`~povineq.stats.get_stats`.

    Args:
        country: ISO3 country code(s) or ``"all"``.
        year: Year(s) or ``"all"``.
        povline: Poverty line value.
        popshare: Population share below the poverty line.
        fill_gaps: Interpolate/extrapolate missing survey years.
        nowcast: Return nowcast estimates (implies ``fill_gaps=True``).
        subgroup: Aggregation sub-group (``"wb_regions"`` or ``"none"``).
        welfare_type: Welfare concept to filter on.
        reporting_level: Reporting geography.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in YYYYMMDD format.
        api_version: API version (only ``"v1"`` supported).
        format: Response format.
    """

    country: str | list[str] = DEFAULT_COUNTRY
    year: str | int | list[int] = DEFAULT_YEAR
    povline: float | None = None
    popshare: float | None = None
    fill_gaps: bool | None = False
    nowcast: bool | None = False
    subgroup: str | None = None
    welfare_type: Literal["all", "income", "consumption"] = "all"
    reporting_level: Literal["all", "national", "urban", "rural"] = "all"
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["arrow", "json", "csv"] = DEFAULT_FORMAT

    @model_validator(mode="after")
    def _apply_business_rules(self) -> StatsParams:
        # popshare cannot be used together with povline
        if self.popshare is not None:
            self.povline = None

        # nowcast = True implies fill_gaps = True
        if self.nowcast:
            self.fill_gaps = True

        # Cannot filter correctly when fill_gaps is False
        if not self.fill_gaps:
            self.nowcast = False

        # subgroup is incompatible with fill_gaps/nowcast
        if self.subgroup is not None:
            self.fill_gaps = None
            self.nowcast = None

        return self

    @field_validator("subgroup")
    @classmethod
    def _validate_subgroup(cls, v: str | None) -> str | None:
        if v is not None and v not in ("wb_regions", "none"):
            raise ValueError("subgroup must be 'wb_regions' or 'none'")
        return v


class CpParams(_BaseParams):
    """Parameters for :func:`~povineq.country_profiles.get_cp`.

    Args:
        country: ISO3 country code(s) or ``"all"``.
        povline: Poverty line value.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in YYYYMMDD format.
        api_version: API version.
        format: Response format.
    """

    country: str | list[str] = DEFAULT_COUNTRY
    povline: float | None = DEFAULT_POVLINE_CP
    version: str | None = None
    ppp_version: int = DEFAULT_PPP_VERSION
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["arrow", "json", "csv"] = DEFAULT_FORMAT

    @model_validator(mode="after")
    def _apply_ppp_default(self) -> CpParams:
        # When ppp_version is 2011 and no poverty line specified, default to 1.9
        if self.povline is None and self.ppp_version == 2011:
            self.povline = DEFAULT_POVLINE_CP_2011
        return self


class CpKiParams(_BaseParams):
    """Parameters for :func:`~povineq.country_profiles.get_cp_ki`.

    Args:
        country: Single ISO3 country code (required).
        povline: Poverty line value.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in YYYYMMDD format.
        api_version: API version.
    """

    country: str
    povline: float | None = DEFAULT_POVLINE_CP
    version: str | None = None
    ppp_version: int = DEFAULT_PPP_VERSION
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"

    @field_validator("country")
    @classmethod
    def _validate_country(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("country is required for get_cp_ki()")
        return v

    @model_validator(mode="after")
    def _apply_ppp_default(self) -> CpKiParams:
        if self.povline is None and self.ppp_version == 2011:
            self.povline = DEFAULT_POVLINE_CP_2011
        return self


class AuxParams(_BaseParams):
    """Parameters for :func:`~povineq.aux.get_aux`.

    Args:
        table: Auxiliary table name. If ``None``, returns a list of available tables.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in YYYYMMDD format.
        api_version: API version.
        format: Response format (arrow not supported for aux).
    """

    table: str | None = None
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["json", "csv"] = DEFAULT_FORMAT_AUX


class AggParams(_BaseParams):
    """Parameters for :func:`~povineq.stats.get_agg`.

    Args:
        year: Year(s) or ``"all"``.
        povline: Poverty line value.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in YYYYMMDD format.
        aggregate: Aggregate name (e.g. ``"fcv"``).
        api_version: API version.
        format: Response format.
    """

    year: str | int | list[int] = DEFAULT_YEAR
    povline: float | None = None
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    aggregate: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["json", "csv"] = "json"
