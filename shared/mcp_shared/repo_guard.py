"""Repository guard utilities for MCP servers."""

from pathlib import Path


class RepoGuard:
    """Guard class for repository access control."""

    def __init__(self, allowed_paths: list[str] | None = None):
        self.allowed_paths = allowed_paths or []

    def is_allowed(self, path: str) -> bool:
        """Check if a path is allowed for access."""
        target = Path(path).resolve()
        for allowed in self.allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                target.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        return False

    def add_allowed_path(self, path: str) -> None:
        """Add a path to the allowlist."""
        self.allowed_paths.append(path)
