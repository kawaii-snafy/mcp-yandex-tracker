"""Yandex Tracker MCP server — a thin wrapper over the REST API v3.

One tool per documented endpoint, the API's own parameter names on the way in,
the API's own JSON on the way out. The single source of truth for every path,
parameter and field is the official documentation:
https://yandex.ru/support/tracker/en/llms.txt
"""

from ._version import __version__
from .client import Tracker, TrackerApiError, TrackerConfig, TrackerConfigError
from .server import get_client, main, mcp

# Importing these registers the tracker:// resources and every tracker_* tool on
# the `mcp` server object above; nothing else in the package pulls them in.
from . import resources as resources  # noqa: E402
from . import tools as tools  # noqa: E402

__all__ = [
    "Tracker",
    "TrackerApiError",
    "TrackerConfig",
    "TrackerConfigError",
    "__version__",
    "get_client",
    "main",
    "mcp",
]
