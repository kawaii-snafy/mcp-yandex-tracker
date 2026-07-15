# Yandex Tracker MCP

Small stdio MCP server for Yandex Tracker. It exposes tools for reading,
searching, creating, updating, commenting on, transitioning, and linking Tracker
issues, plus read-only reference lookups (queues, users, statuses, types,
priorities, fields, versions, components).

## Usage with Codex

Add the server to `~/.codex/config.toml`:

```toml
[mcp_servers.yandex-tracker]
command = "uvx"
args = ["mcp-yandex-tracker"]

[mcp_servers.yandex-tracker.env]
YANDEX_TRACKER_TOKEN = "..."
YANDEX_TRACKER_CLOUD_ORG_ID = "..."
```

To run the latest unreleased code straight from source instead, replace the
`args` line with:

```toml
args = ["--from", "git+https://github.com/kawaii-snafy/mcp-yandex-tracker.git", "mcp-yandex-tracker"]
```

For a non-cloud organization, use `YANDEX_TRACKER_ORG_ID` instead of
`YANDEX_TRACKER_CLOUD_ORG_ID`.

Restart Codex after changing the config. The server exposes tools named
`tracker_*`, such as `tracker_get_issue`, `tracker_search_issues`, and
`tracker_add_comment`.

## Usage with Claude Code

Add the server with the Claude Code CLI:

```sh
claude mcp add --transport stdio \
  --env YANDEX_TRACKER_TOKEN="..." \
  --env YANDEX_TRACKER_CLOUD_ORG_ID="..." \
  yandex-tracker \
  -- uvx mcp-yandex-tracker
```

For a non-cloud organization, use `--env YANDEX_TRACKER_ORG_ID="..."` instead
of `YANDEX_TRACKER_CLOUD_ORG_ID`.

Verify the Claude Code registration:

```sh
claude mcp list
claude mcp get yandex-tracker
```

Inside Claude Code, use `/mcp` to check the server connection and tools.

## Environment

Required:

- `YANDEX_TRACKER_TOKEN`: OAuth or IAM token.
- One organization id: `YANDEX_TRACKER_CLOUD_ORG_ID` for cloud organizations or
  `YANDEX_TRACKER_ORG_ID` for non-cloud organizations.

Optional:

- `YANDEX_TRACKER_AUTH_SCHEME`: `OAuth` by default. Use `Bearer` for IAM tokens.
- `YANDEX_TRACKER_BASE_URL`: `https://api.tracker.yandex.net` by default.
- `YANDEX_TRACKER_TIMEOUT`: `30` by default.

## Verify locally

Run the MCP server and ask for its tool list. MCP requires the `initialize`
handshake before any other request, so send it (and the `initialized`
notification) first:

```sh
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
| YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." uvx mcp-yandex-tracker
```

The second response line should be a JSON-RPC object with `tracker_*` tools. The
server is stdio-only, so stdout is reserved for MCP JSON-RPC messages (logs go
to stderr).

## Documentation

Deeper docs live in [`docs/`](docs/README.md):

- [INTEGRATION.md](docs/INTEGRATION.md) — connect the server to a host.
- [TOOLS.md](docs/TOOLS.md) — full tool reference with arguments.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the server works internally.
- [EXTENDING.md](docs/EXTENDING.md) — add tools, rules, and scaling notes.

## Development

```sh
git clone git@github.com:kawaii-snafy/mcp-yandex-tracker.git
cd mcp-yandex-tracker
python3 -m venv .venv
.venv/bin/python -m pip install -e .
python3 -m unittest discover -s tests
```
