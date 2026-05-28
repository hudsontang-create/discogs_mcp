"""HTTP client for the Discogs API."""

import httpx

from .config import config


class DiscogsClient:
    """Async HTTP client for Discogs API requests."""

    def __init__(self) -> None:
        self.base_url = config.api_url
        self.headers = {
            "Accept": "application/vnd.discogs.v2.discogs+json",
            "Authorization": f"Discogs token={config.personal_access_token}",
            "Content-Type": "application/json",
            "User-Agent": config.user_agent,
        }
        self.default_per_page = config.default_per_page

    async def get(
        self, path: str, params: dict | None = None
    ) -> dict | list | str:
        """Make a GET request to the Discogs API."""
        if params is None:
            params = {}

        # Set default per_page if not specified
        if "per_page" not in params:
            params["per_page"] = self.default_per_page

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            self._raise_for_status(resp)
            return resp.json()

    async def post(
        self, path: str, body: dict | None = None
    ) -> dict | list | str:
        """Make a POST request to the Discogs API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                headers=self.headers,
                json=body,
                timeout=30.0,
            )
            self._raise_for_status(resp)
            if resp.status_code == 204:
                return {}
            return resp.json()

    async def delete(self, path: str) -> None:
        """Make a DELETE request to the Discogs API."""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=30.0,
            )
            self._raise_for_status(resp)

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """Raise a descriptive error for non-2xx responses."""
        if resp.is_success:
            return

        try:
            body = resp.json()
            message = body.get("message", resp.text)
        except Exception:
            message = resp.text

        status = resp.status_code
        if status == 401:
            raise ValueError(f"Authentication failed: {message}")
        elif status == 403:
            raise ValueError(f"Insufficient permissions: {message}")
        elif status == 404:
            raise ValueError(f"Resource not found: {message}")
        elif status == 422:
            raise ValueError(f"Validation failed: {message}")
        elif status == 429:
            raise ValueError(f"Rate limit exceeded: {message}")
        else:
            raise ValueError(
                f"Discogs API error ({status}): {message}"
            )
