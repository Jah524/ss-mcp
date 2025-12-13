"""Unit tests for code_review server."""

from unittest.mock import MagicMock, patch

import pytest

from code_review.server import (
    _changed_files_from_unified_diff,
    _read_worktree_files,
    _resolve_repo_root,
    repo_info,
)


class TestChangedFilesFromUnifiedDiff:
    """Tests for _changed_files_from_unified_diff function."""

    def test_single_file(self):
        diff = """
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1 +1 @@
-old
+new
"""
        files = _changed_files_from_unified_diff(diff)
        assert files == ["foo.py"]

    def test_multiple_files(self):
        diff = """
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1 +1 @@
-old
+new
diff --git a/bar.py b/bar.py
--- a/bar.py
+++ b/bar.py
@@ -1 +1 @@
-old
+new
"""
        files = _changed_files_from_unified_diff(diff)
        assert files == ["foo.py", "bar.py"]

    def test_new_file(self):
        diff = """
diff --git a/new_file.py b/new_file.py
new file mode 100644
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1 @@
+content
"""
        files = _changed_files_from_unified_diff(diff)
        assert files == ["new_file.py"]

    def test_empty_diff(self):
        diff = ""
        files = _changed_files_from_unified_diff(diff)
        assert files == []

    def test_deduplication(self):
        diff = """
+++ b/foo.py
+++ b/foo.py
+++ b/bar.py
"""
        files = _changed_files_from_unified_diff(diff)
        assert files == ["foo.py", "bar.py"]


class TestResolveRepoRoot:
    """Tests for _resolve_repo_root function."""

    def test_nonexistent_path(self):
        with pytest.raises(ValueError, match="not found"):
            _resolve_repo_root("/nonexistent/path/to/repo")

    def test_not_a_directory(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not found"):
            _resolve_repo_root(str(file_path))

    @patch("code_review.server._sh")
    def test_valid_repo(self, mock_sh, tmp_path):
        mock_sh.return_value = str(tmp_path) + "\n"
        result = _resolve_repo_root(str(tmp_path))
        assert result == tmp_path


class TestReadWorktreeFiles:
    """Tests for _read_worktree_files function."""

    def test_reads_existing_files(self, tmp_path):
        (tmp_path / "test.py").write_text("content")
        result = _read_worktree_files(tmp_path, ["test.py"])
        assert result == {"test.py": "content"}

    def test_skips_nonexistent_files(self, tmp_path):
        result = _read_worktree_files(tmp_path, ["nonexistent.py"])
        assert result == {}

    def test_respects_max_bytes(self, tmp_path):
        (tmp_path / "big.py").write_text("x" * 1000)
        with patch("code_review.server.MAX_CTX_BYTES", 100):
            result = _read_worktree_files(tmp_path, ["big.py"])
            assert result == {}

    def test_prevents_path_traversal(self, tmp_path):
        result = _read_worktree_files(tmp_path, ["../etc/passwd"])
        assert result == {}


class TestRepoInfo:
    """Tests for repo_info function."""

    @patch("code_review.server._sh")
    @patch("code_review.server._resolve_repo_root")
    def test_returns_repo_info(self, mock_resolve, mock_sh):
        from pathlib import Path

        mock_resolve.return_value = Path("/tmp/repo")
        mock_sh.side_effect = [
            "/tmp/repo\n",  # toplevel
            "main\n",  # branch
            "origin\tgit@github.com:user/repo.git (fetch)\n",  # remotes
        ]

        result = repo_info("/tmp/repo")

        assert result["toplevel"] == "/tmp/repo"
        assert result["branch"] == "main"
        assert "origin" in result["remotes"]
