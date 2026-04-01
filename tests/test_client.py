"""Tests for _client.py — server selection and client construction."""

from __future__ import annotations

import pytest

import httpx

from povineq._client import get_client, select_base_url
from povineq._constants import PROD_URL, USER_AGENT


class TestGetClient:
    def test_returns_httpx_client(self):
        client = get_client()
        assert isinstance(client, httpx.Client)

    def test_default_base_url_is_prod(self):
        client = get_client()
        assert str(client.base_url).rstrip("/") == PROD_URL

    def test_user_agent_header_set(self):
        client = get_client()
        assert client.headers["user-agent"] == USER_AGENT

    def test_timeout_is_60(self):
        client = get_client()
        assert client.timeout.read == pytest.approx(60.0)

    def test_qa_server_uses_env_url(self, monkeypatch):
        monkeypatch.setenv("PIP_QA_URL", "https://qa.example.com/pip")
        client = get_client("qa")
        assert "qa.example.com" in str(client.base_url)

    def test_dev_server_uses_env_url(self, monkeypatch):
        monkeypatch.setenv("PIP_DEV_URL", "https://dev.example.com/pip")
        client = get_client("dev")
        assert "dev.example.com" in str(client.base_url)


class TestSelectBaseUrl:
    def test_none_returns_prod(self):
        assert select_base_url(None) == PROD_URL

    def test_prod_returns_prod(self):
        assert select_base_url("prod") == PROD_URL

    def test_invalid_server_raises(self):
        with pytest.raises(ValueError, match="server must be"):
            select_base_url("staging")

    @pytest.mark.parametrize("server,env_var,url", [
        ("qa", "PIP_QA_URL", "https://qa.example.com/pip"),
        ("dev", "PIP_DEV_URL", "https://dev.example.com/pip"),
    ])
    def test_server_reads_env_var(self, server, env_var, url, monkeypatch):
        monkeypatch.setenv(env_var, url)
        assert select_base_url(server) == url

    @pytest.mark.parametrize("server,env_var", [
        ("qa", "PIP_QA_URL"),
        ("dev", "PIP_DEV_URL"),
    ])
    def test_server_missing_env_raises(self, server, env_var, monkeypatch):
        monkeypatch.delenv(env_var, raising=False)
        with pytest.raises(EnvironmentError, match=env_var):
            select_base_url(server)
