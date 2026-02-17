"""Inoreader MCP Server - FastMCP implementation."""

import sys

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan


@lifespan
async def app_lifespan(server: FastMCP):
    """Application lifespan managing configuration.

    Validates that required environment variables are set.
    """
    from .config import Config

    Config.validate()

    print("Inoreader MCP Server", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("Version: 0.1.0 (FastMCP)", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(file=sys.stderr)

    yield {}


mcp = FastMCP(
    "Inoreader",
    lifespan=app_lifespan,
)


__all__ = ["mcp"]
