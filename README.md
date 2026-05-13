# Yandex Tracker MCP

Small stdio MCP server for Yandex Tracker. It exposes tools for reading,
searching, creating, updating, commenting on, and transitioning Tracker issues.

## Configuration

Set these environment variables before starting the server:

```sh
export YANDEX_TRACKER_TOKEN="..."
export YANDEX_TRACKER_ORG_ID="..."
```

For cloud organizations, use `YANDEX_TRACKER_CLOUD_ORG_ID` instead of
`YANDEX_TRACKER_ORG_ID`. Optional variables:

- `YANDEX_TRACKER_AUTH_SCHEME`, default `OAuth`
- `YANDEX_TRACKER_BASE_URL`, default `https://api.tracker.yandex.net/v2`
- `YANDEX_TRACKER_TIMEOUT`, default `30`

## Codex MCP config

```toml
[mcp_servers.yandex-tracker]
command = "python3"
args = ["-m", "yandex_tracker_mcp_server"]
cwd = "/Users/snafy/Projects/yandex-tracker-mcp"
env = { YANDEX_TRACKER_TOKEN = "...", YANDEX_TRACKER_ORG_ID = "..." }
```

## Development

```sh
python3 -m unittest discover -s tests
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n' | python3 -m yandex_tracker_mcp_server
```
