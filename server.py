#!/usr/bin/env python3
"""Discogs MCP Server runner.

Run directly: python3 server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from discogs_mcp_server.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run(transport="stdio")
