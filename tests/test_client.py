"""Tests for _client.py — server selection and client construction."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from povineq._client import select_base_url
from povineq._constants import PROD_URL


class TestSelectBaseUrl:
    def test_none_returns_prod(self):
        assert select_base_url(None) == PROD_URL

    def test_prod_returns_prod(self):
        assert select_base_url("prod") == PROD_URL

    def test_invalid_server_raises(self):
        with pytest.raises(ValueError, match="server must be"):
            select_base_url("staging")

    def test_qa_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("PIP_QA_URL", "https://qa.example.com/pip")
        assert select_base_url("qa") == "https://qa.example.com/pip"

    def test_dev_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("PIP_DEV_URL", "https://dev.example.com/pip")
        assert select_base_url("dev") == "https://dev.example.com/pip"

    def test_qa_missing_env_raises(self, monkeypatch):
        monkeypatch.delenv("PIP_QA_URL", raising=False)
        with pytest.raises(EnvironmentError, match="PIP_QA_URL"):
            select_base_url("qa")

    def test_dev_missing_env_raises(self, monkeypatch):
        monkeypatch.delenv("PIP_DEV_URL", raising=False)
        with pytest.raises(EnvironmentError, match="PIP_DEV_URL"):
            select_base_url("dev")
