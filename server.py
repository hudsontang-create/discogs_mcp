"""
Discogs MCP Server — Python Implementation

A consolidated 2-tool MCP server for the Discogs API.
- discogs_get: 26 read operations via resource_type routing
- discogs_update: 8 collection write operations via action routing

Requires: pip install mcp httpx python-dotenv
"""

import json
import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Configuration ───────────────────────────────────────────────────────

load_dotenv(verbose=False)

DISCOGS_TOKEN = os.environ.get("DISCOGS_PERSONAL_ACCESS_TOKEN", "")
if not DISCOGS_TOKEN:
    print("ERROR: Missing DISCOGS_PERSONAL_ACCESS_TOKEN env var", file=sys.stderr)
    sys.exit(1)

API_URL = os.environ.get("DISCOGS_API_URL", "https://api.discogs.com")
USER_AGENT = os.environ.get("DISCOGS_USER_AGENT", "DiscogsMCPServer/0.1.0-python")
DEFAULT_PER_PAGE = int(os.environ.get("DISCOGS_DEFAULT_PER_PAGE", "5"))
SERVER_NAME = os.environ.get("SERVER_NAME", "Discogs MCP Server")

HEADERS = {
    "Accept": "application/vnd.discogs.v2.discogs+json",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
}

mcp = FastMCP(SERVER_NAME)


# ── HTTP Client ─────────────────────────────────────────────────────────


def _raise_for_status(resp: httpx.Response) -> None:
    """Raise a descriptive error for non-2xx responses."""
    if resp.is_success:
        return
    try:
        body = resp.json()
        message = body.get("message", resp.text)
    except Exception:
        message = resp.text
    status = resp.status_code
    error_map = {401: "Authentication failed", 403: "Insufficient permissions",
                 404: "Resource not found", 422: "Validation failed",
                 429: "Rate limit exceeded"}
    prefix = error_map.get(status, f"Discogs API error ({status})")
    raise ValueError(f"{prefix}: {message}")


async def _get(path: str, params: dict | None = None) -> Any:
    """GET request to Discogs API."""
    if params is None:
        params = {}
    if "per_page" not in params:
        params["per_page"] = DEFAULT_PER_PAGE
    params = {k: v for k, v in params.items() if v is not None}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}{path}", headers=HEADERS, params=params, timeout=30.0)
        _raise_for_status(resp)
        return resp.json()


async def _post(path: str, body: dict | None = None) -> Any:
    """POST request to Discogs API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}{path}", headers=HEADERS, json=body, timeout=30.0)
        _raise_for_status(resp)
        return resp.json() if resp.status_code != 204 else {}


async def _delete(path: str) -> None:
    """DELETE request to Discogs API."""
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{API_URL}{path}", headers=HEADERS, timeout=30.0)
        _raise_for_status(resp)


def _json(data: Any) -> str:
    return json.dumps(data, indent=2)


# ── Routing Tables ──────────────────────────────────────────────────────

GET_ROUTES: dict[str, tuple[str, list[str]]] = {
    # User identity
    "user_identity": ("/oauth/identity", []),
    "user_profile": ("/users/{username}", []),
    "user_submissions": ("/users/{username}/submissions", []),
    "user_contributions": ("/users/{username}/contributions", ["page", "per_page", "sort", "sort_order"]),
    # Database
    "release": ("/releases/{release_id}", ["curr_abbr"]),
    "release_rating_by_user": ("/releases/{release_id}/rating/{username}", []),
    "release_community_rating": ("/releases/{release_id}/rating", []),
    "master_release": ("/masters/{master_id}", []),
    "master_release_versions": ("/masters/{master_id}/versions", ["page", "per_page", "sort", "sort_order", "format", "label", "released", "country"]),
    "artist": ("/artists/{artist_id}", []),
    "artist_releases": ("/artists/{artist_id}/releases", ["page", "per_page", "sort_order"]),
    "label": ("/labels/{label_id}", []),
    "label_releases": ("/labels/{label_id}/releases", ["page", "per_page", "sort_order"]),
    "search": ("/database/search", ["q", "type", "title", "release_title", "credit", "artist", "anv", "label", "genre", "style", "country", "year", "format", "catno", "barcode", "track", "submitter", "contributor", "page", "per_page"]),
    # Collection
    "collection_folders": ("/users/{username}/collection/folders", []),
    "collection_folder": ("/users/{username}/collection/folders/{folder_id}", []),
    "collection_items": ("/users/{username}/collection/folders/{folder_id}/releases", ["page", "per_page", "sort", "sort_order"]),
    "collection_release": ("/users/{username}/collection/releases/{release_id}", ["page", "per_page"]),
    "collection_custom_fields": ("/users/{username}/collection/fields", []),
    "collection_value": ("/users/{username}/collection/value", []),
    # Wantlist
    "wantlist": ("/users/{username}/wants", ["page", "per_page", "sort", "sort_order"]),
    # Lists
    "user_lists": ("/users/{username}/lists", []),
    "list": ("/lists/{list_id}", []),
    # Marketplace
    "marketplace_release_stats": ("/marketplace/stats/{release_id}", ["curr_abbr"]),
    "user_inventory": ("/users/{username}/inventory", ["page", "per_page", "status", "sort", "sort_order"]),
    "marketplace_listing": ("/marketplace/listings/{listing_id}", ["curr_abbr"]),
}

UPDATE_ROUTES: dict[str, tuple[str, str, list[str]]] = {
    "create_folder": ("POST", "/users/{username}/collection/folders", ["name"]),
    "edit_folder": ("POST", "/users/{username}/collection/folders/{folder_id}", ["name"]),
    "delete_folder": ("DELETE", "/users/{username}/collection/folders/{folder_id}", []),
    "add_release_to_folder": ("POST", "/users/{username}/collection/folders/{folder_id}/releases/{release_id}", []),
    "remove_release_from_folder": ("DELETE", "/users/{username}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}", []),
    "rate_release": ("POST", "/users/{username}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}", ["rating"]),
    "move_release": ("POST", "/users/{username}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}", ["folder_id:destination_folder_id"]),
    "edit_custom_field": ("POST", "/users/{username}/collection/folders/{folder_id}/releases/{release_id}/instances/{instance_id}/fields/{field_id}", ["value"]),
}


# ── Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def discogs_get(resource_type: str, params: dict | None = None) -> str:
    """Retrieve data from the Discogs API.

    Args:
        resource_type: The type of resource to fetch. One of:
            User: user_identity, user_profile, user_submissions, user_contributions
            Database: release, release_rating_by_user, release_community_rating,
                master_release, master_release_versions, artist, artist_releases,
                label, label_releases, search
            Collection: collection_folders, collection_folder, collection_items,
                collection_release, collection_custom_fields, collection_value
            Wantlist: wantlist
            Lists: user_lists, list
            Marketplace: marketplace_release_stats, user_inventory, marketplace_listing
        params: Parameters dict. Path params (e.g. username, release_id, artist_id)
            are used to build the URL. Query params (e.g. page, per_page, sort)
            are passed as query string. Examples:
            - {"username": "rodneyfool"} for user_profile
            - {"release_id": 249504} for release
            - {"q": "Nirvana", "type": "artist"} for search
            - {"username": "rodneyfool", "folder_id": 0} for collection_items
    """
    if resource_type not in GET_ROUTES:
        available = ", ".join(sorted(GET_ROUTES.keys()))
        raise ValueError(f"Unknown resource_type '{resource_type}'. Available: {available}")

    if params is None:
        params = {}

    path_template, query_keys = GET_ROUTES[resource_type]

    try:
        path = path_template.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing required parameter {e} for resource_type '{resource_type}'. Path: {path_template}")

    query_params = {k: params[k] for k in query_keys if k in params}
    data = await _get(path, query_params if query_params else None)
    return _json(data)


@mcp.tool()
async def discogs_update(action: str, params: dict | None = None) -> str:
    """Modify data in your Discogs collection.

    Args:
        action: The write operation to perform. One of:
            create_folder — Create a collection folder (params: username, name)
            edit_folder — Rename a folder (params: username, folder_id, name)
            delete_folder — Delete an empty folder (params: username, folder_id)
            add_release_to_folder — Add release to folder (params: username, folder_id, release_id)
            remove_release_from_folder — Remove release (params: username, folder_id, release_id, instance_id)
            rate_release — Rate 1-5 (params: username, folder_id, release_id, instance_id, rating)
            move_release — Move to another folder (params: username, folder_id, release_id, instance_id, destination_folder_id)
            edit_custom_field — Edit custom field (params: username, folder_id, release_id, instance_id, field_id, value)
        params: Parameters dict with the required fields for the action.
    """
    if action not in UPDATE_ROUTES:
        available = ", ".join(sorted(UPDATE_ROUTES.keys()))
        raise ValueError(f"Unknown action '{action}'. Available: {available}")

    if params is None:
        params = {}

    method, path_template, body_keys = UPDATE_ROUTES[action]

    try:
        path = path_template.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing required parameter {e} for action '{action}'. Path: {path_template}")

    body = {}
    for key in body_keys:
        if ":" in key:
            body_key, param_key = key.split(":", 1)
            if param_key in params:
                body[body_key] = params[param_key]
        else:
            if key in params:
                body[key] = params[key]

    if method == "DELETE":
        await _delete(path)
        return json.dumps({"status": "success", "action": action})
    else:
        data = await _post(path, body=body if body else None)
        return _json(data) if data else json.dumps({"status": "success", "action": action})


# ── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
