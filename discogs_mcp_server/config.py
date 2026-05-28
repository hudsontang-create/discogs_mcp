"""Configuration for the Discogs MCP Server."""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env silently — never write to stdout
load_dotenv(verbose=False)


@dataclass
class Config:
    """Server configuration loaded from environment variables."""

    api_url: str
    personal_access_token: str
    user_agent: str
    default_per_page: int
    server_name: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("DISCOGS_PERSONAL_ACCESS_TOKEN", "")
        if not token:
            # Write to stderr, never stdout (stdout is the MCP transport)
            print(
                "ERROR: Missing DISCOGS_PERSONAL_ACCESS_TOKEN env var",
                file=sys.stderr,
            )
            sys.exit(1)
        return cls(
            api_url=os.environ.get(
                "DISCOGS_API_URL", "https://api.discogs.com"
            ),
            personal_access_token=token,
            user_agent=os.environ.get(
                "DISCOGS_USER_AGENT", "DiscogsMCPServer/0.1.0-python"
            ),
            default_per_page=int(
                os.environ.get("DISCOGS_DEFAULT_PER_PAGE", "5")
            ),
            server_name=os.environ.get(
                "SERVER_NAME", "Discogs MCP Server"
            ),
        )


config = Config.from_env()
