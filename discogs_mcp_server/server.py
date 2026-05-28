"""Discogs MCP Server - consolidated tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import DiscogsClient
from .config import config

mcp = FastMCP(config.server_name)


def _json(data: Any) -> str:
    """Serialize response data to JSON string."""
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Routing tables
# ---------------------------------------------------------------------------

# Maps resource_type -> (path_template, query_param_keys)
# Path templates use {key} for substitution from params
GET_ROUTES: dict[str, tuple[str, list[str]]] = {
    # User identity
    "user_identity": ("/oauth/identity", []),
    "user_profile": ("/users/{username}", []),
    "user_submissions": ("/users/{username}/submissions", []),
    "user_contributions": (
        "/users/{username}/contributions",
        ["page", "per_page", "sort", "sort_order"],
    ),
    # Database
    "release": ("/releases/{release_id}", ["curr_abbr"]),
    "release_rating_by_user": (
        "/releases/{release_id}/rating/{username}",
        [],
    ),
    "release_community_rating": ("/releases/{release_id}/rating", []),
    "master_release": ("/masters/{master_id}", []),
    "master_release_versions": (
        "/masters/{master_id}/versions",
        ["page", "per_page", "sort", "sort_order",
         "format", "label", "released", "country"],
    ),
    "artist": ("/artists/{artist_id}", []),
    "artist_releases": (
        "/artists/{artist_id}/releases",
        ["page", "per_page", "sort_order"],
    ),
    "label": ("/labels/{label_id}", []),
    "label_releases": (
        "/labels/{label_id}/releases",
        ["page", "per_page", "sort_order"],
    ),
    "search": (
        "/database/search",
        ["q", "type", "title", "release_title", "credit",
         "artist", "anv", "label", "genre", "style",
         "country", "year", "format", "catno", "barcode",
         "track", "submitter", "contributor", "page", "per_page"],
    ),
    # Collection
    "collection_folders": ("/users/{username}/collection/folders", []),
    "collection_folder": (
        "/users/{username}/collection/folders/{folder_id}",
        [],
    ),
    "collection_items": (
        "/users/{username}/collection/folders/{folder_id}/releases",
        ["page", "per_page", "sort", "sort_order"],
    ),
    "collection_release": (
        "/users/{username}/collection/releases/{release_id}",
        ["page", "per_page"],
    ),
    "collection_custom_fields": (
        "/users/{username}/collection/fields",
        [],
    ),
    "collection_value": ("/users/{username}/collection/value", []),
    # Wantlist
    "wantlist": (
        "/users/{username}/wants",
        ["page", "per_page", "sort", "sort_order"],
    ),
    # Lists
    "user_lists": ("/users/{username}/lists", []),
    "list": ("/lists/{list_id}", []),
    # Marketplace
    "marketplace_release_stats": (
        "/marketplace/stats/{release_id}",
        ["curr_abbr"],
    ),
    "user_inventory": (
        "/users/{username}/inventory",
        ["page", "per_page", "status", "sort", "sort_order"],
    ),
    "marketplace_listing": (
        "/marketplace/listings/{listing_id}",
        ["curr_abbr"],
    ),
}


# Maps action -> (method, path_template, body_keys)
UPDATE_ROUTES: dict[str, tuple[str, str, list[str]]] = {
    "create_folder": (
        "POST",
        "/users/{username}/collection/folders",
        ["name"],
    ),
    "edit_folder": (
        "POST",
        "/users/{username}/collection/folders/{folder_id}",
        ["name"],
    ),
    "delete_folder": (
        "DELETE",
        "/users/{username}/collection/folders/{folder_id}",
        [],
    ),
    "add_release_to_folder": (
        "POST",
        "/users/{username}/collection/folders/{folder_id}/releases/{release_id}",
        [],
    ),
    "remove_release_from_folder": (
        "DELETE",
        "/users/{username}/collection/folders/{folder_id}"
        "/releases/{release_id}/instances/{instance_id}",
        [],
    ),
    "rate_release": (
        "POST",
        "/users/{username}/collection/folders/{folder_id}"
        "/releases/{release_id}/instances/{instance_id}",
        ["rating"],
    ),
    "move_release": (
        "POST",
        "/users/{username}/collection/folders/{folder_id}"
        "/releases/{release_id}/instances/{instance_id}",
        ["folder_id:destination_folder_id"],
    ),
    "edit_custom_field": (
        "POST",
        "/users/{username}/collection/folders/{folder_id}"
        "/releases/{release_id}/instances/{instance_id}"
        "/fields/{field_id}",
        ["value"],
    ),
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

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
        raise ValueError(
            f"Unknown resource_type '{resource_type}'. "
            f"Available: {available}"
        )

    if params is None:
        params = {}

    path_template, query_keys = GET_ROUTES[resource_type]

    # Build path by substituting {key} placeholders
    try:
        path = path_template.format(**params)
    except KeyError as e:
        raise ValueError(
            f"Missing required parameter {e} for resource_type "
            f"'{resource_type}'. Path template: {path_template}"
        )

    # Extract query params
    query_params = {k: params[k] for k in query_keys if k in params}

    client = DiscogsClient()
    data = await client.get(path, query_params if query_params else None)
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
        raise ValueError(
            f"Unknown action '{action}'. Available: {available}"
        )

    if params is None:
        params = {}

    method, path_template, body_keys = UPDATE_ROUTES[action]

    # Build path by substituting {key} placeholders
    try:
        path = path_template.format(**params)
    except KeyError as e:
        raise ValueError(
            f"Missing required parameter {e} for action "
            f"'{action}'. Path template: {path_template}"
        )

    # Build request body from body_keys
    body = {}
    for key in body_keys:
        # Support key mapping like "folder_id:destination_folder_id"
        if ":" in key:
            body_key, param_key = key.split(":", 1)
            if param_key in params:
                body[body_key] = params[param_key]
        else:
            if key in params:
                body[key] = params[key]

    client = DiscogsClient()
    if method == "DELETE":
        await client.delete(path)
        return json.dumps({"status": "success", "action": action})
    else:
        data = await client.post(path, body=body if body else None)
        if data:
            return _json(data)
        return json.dumps({"status": "success", "action": action})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
