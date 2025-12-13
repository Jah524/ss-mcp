"""Resource limits and constraints for MCP servers."""


class Limits:
    """Resource limits configuration."""

    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_MAX_FILES = 100
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_files: int = DEFAULT_MAX_FILES,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.timeout = timeout

    def check_file_size(self, size: int) -> bool:
        """Check if file size is within limits."""
        return size <= self.max_file_size

    def check_file_count(self, count: int) -> bool:
        """Check if file count is within limits."""
        return count <= self.max_files
