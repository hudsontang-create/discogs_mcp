# Discogs MCP Server (Python)

A Python MCP server for the Discogs API. Port of [discogs-mcp-server](https://github.com/cswkim/discogs-mcp-server).

## Features

- Search the Discogs database (artists, releases, labels, masters)
- Browse user profiles, collections, wantlists, and lists
- Manage collection folders and releases (create, edit, delete, move, rate)
- View marketplace listings and release stats
- **Only 2 tools** — consolidated via `resource_type` / `action` routing

## Prerequisites

- Python 3.10+
- `mcp`, `httpx`, and `python-dotenv` packages
- A Discogs personal access token ([get one here](https://www.discogs.com/settings/developers))

## Installation

```bash
pip install mcp httpx python-dotenv
```

## Configuration

Set your token as an environment variable or in a `.env` file:

```bash
export DISCOGS_PERSONAL_ACCESS_TOKEN=your_token_here
```

## MCP Client Configuration (Kiro, Claude, etc.)

```json
{
  "mcpServers": {
    "discogs": {
      "command": "python3",
      "args": ["/path/to/discogs-mcp-server-python/server.py"],
      "env": {
        "DISCOGS_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"
      }
    }
  }
}
```

## Tools

### `discogs_get` — Read data

Params: `resource_type` + `params` dict.

| resource_type | Required params | Optional params |
|---|---|---|
| `user_identity` | — | — |
| `user_profile` | username | — |
| `user_submissions` | username | — |
| `user_contributions` | username | page, per_page, sort, sort_order |
| `release` | release_id | curr_abbr |
| `release_rating_by_user` | release_id, username | — |
| `release_community_rating` | release_id | — |
| `master_release` | master_id | — |
| `master_release_versions` | master_id | page, per_page, sort, sort_order, format, label, released, country |
| `artist` | artist_id | — |
| `artist_releases` | artist_id | page, per_page, sort_order |
| `label` | label_id | — |
| `label_releases` | label_id | page, per_page, sort_order |
| `search` | — | q, type, title, artist, label, genre, style, country, year, format, catno, barcode, page, per_page |
| `collection_folders` | username | — |
| `collection_folder` | username, folder_id | — |
| `collection_items` | username, folder_id | page, per_page, sort, sort_order |
| `collection_release` | username, release_id | page, per_page |
| `collection_custom_fields` | username | — |
| `collection_value` | username | — |
| `wantlist` | username | page, per_page, sort, sort_order |
| `user_lists` | username | — |
| `list` | list_id | — |
| `marketplace_release_stats` | release_id | curr_abbr |
| `user_inventory` | username | page, per_page, status, sort, sort_order |
| `marketplace_listing` | listing_id | curr_abbr |

### `discogs_update` — Modify collection data

Params: `action` + `params` dict.

| action | Required params |
|---|---|
| `create_folder` | username, name |
| `edit_folder` | username, folder_id, name |
| `delete_folder` | username, folder_id |
| `add_release_to_folder` | username, folder_id, release_id |
| `remove_release_from_folder` | username, folder_id, release_id, instance_id |
| `rate_release` | username, folder_id, release_id, instance_id, rating |
| `move_release` | username, folder_id, release_id, instance_id, destination_folder_id |
| `edit_custom_field` | username, folder_id, release_id, instance_id, field_id, value |

## Example Usage

```
"Search for Nirvana albums"
→ discogs_get(resource_type="search", params={"q": "Nirvana", "type": "master"})

"Show my collection folders"
→ discogs_get(resource_type="collection_folders", params={"username": "myuser"})

"Rate this release 5 stars"
→ discogs_update(action="rate_release", params={"username": "myuser", "folder_id": 1, "release_id": 249504, "instance_id": 1, "rating": 5})
```

## License

MIT
