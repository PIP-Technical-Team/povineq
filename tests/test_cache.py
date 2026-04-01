"""Tests for cache management (_cache.py)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from povineq._cache import _cache_dir, delete_cache, get_cache_info


class TestCacheDir:
    def test_returns_path(self, tmp_path):
        with patch("povineq._cache.user_cache_dir", return_value=str(tmp_path / "test_cache")):
            path = _cache_dir()
        assert isinstance(path, Path)
        assert path.exists()

    def test_creates_directory(self, tmp_path):
        target = tmp_path / "new_cache_dir"
        assert not target.exists()
        with patch("povineq._cache.user_cache_dir", return_value=str(target)):
            path = _cache_dir()
        assert path.exists()


class TestDeleteCache:
    def test_empty_cache_message(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr("povineq._cache._cache_dir", lambda: tmp_path)
        delete_cache()
        captured = capsys.readouterr()
        assert "empty" in captured.out.lower() or "nothing" in captured.out.lower()

    def test_deletes_files(self, tmp_path, monkeypatch, capsys):
        # Create some dummy files
        (tmp_path / "cache1.dat").write_bytes(b"x")
        (tmp_path / "cache2.dat").write_bytes(b"y")
        monkeypatch.setattr("povineq._cache._cache_dir", lambda: tmp_path)
        delete_cache()
        remaining = list(tmp_path.iterdir())
        assert remaining == []


class TestGetCacheInfo:
    def test_empty_cache_returns_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr("povineq._cache._cache_dir", lambda: tmp_path)
        info = get_cache_info()
        assert info["n_files"] == 0
        assert info["total_bytes"] == 0
        assert str(tmp_path) in info["path"]

    def test_non_empty_cache(self, tmp_path, monkeypatch):
        (tmp_path / "cache1.dat").write_bytes(b"hello")
        monkeypatch.setattr("povineq._cache._cache_dir", lambda: tmp_path)
        info = get_cache_info()
        assert info["n_files"] == 1
        assert info["total_bytes"] == 5
