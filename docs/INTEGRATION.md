# Integration guide

How to connect Yandex Tracker MCP to an MCP host. For the tools themselves see
[TOOLS.md](TOOLS.md).

## Transport

The server is **stdio-only**. It reads newline-delimited JSON-RPC 2.0 requests
from stdin and writes responses to stdout. There is no HTTP/SSE transport.
Because stdout is reserved for protocol traffic, all diagnostics go to stderr —
if you wrap the server, do not merge stderr into stdout.

## Environment

Configuration comes entirely from environment variables, read fresh on every
tool call (`TrackerConfig.from_env`).

### Required

| Variable                        | Purpose                                              |
| ------------------------------- | ---------------------------------------------------- |
| `YANDEX_TRACKER_TOKEN`          | OAuth or IAM token.                                  |
| `YANDEX_TRACKER_CLOUD_ORG_ID`   | Cloud organization id. Use this **or** the next one. |
| `YANDEX_TRACKER_ORG_ID`         | Non-cloud organization id.                           |

Exactly one org id must be set; if neither is present the tool call fails with a
config error.

### Optional

| Variable                     | Default                          | Notes                                                            |
| ---------------------------- | -------------------------------- | --------------------------------------------------------------- |
| `YANDEX_TRACKER_AUTH_SCHEME` | `OAuth`                          | Set to `Bearer` for IAM tokens (routes the token as `iam_token`). |
| `YANDEX_TRACKER_BASE_URL`    | `https://api.tracker.yandex.net` | A trailing `/v2` or `/v3` is split off into the SDK `api_version` (default `v2`). |
| `YANDEX_TRACKER_TIMEOUT`     | `30`                             | Request timeout in seconds (float).                             |

## Host configuration

### Codex

Add to `~/.codex/config.toml` (see `codex-mcp.example.toml` in the repo root):

```toml
[mcp_servers.yandex-tracker]
command = "uvx"
args = ["mcp-yandex-tracker"]

[mcp_servers.yandex-tracker.env]
YANDEX_TRACKER_TOKEN = "..."
YANDEX_TRACKER_CLOUD_ORG_ID = "..."
```

To run from source instead of the published package, use
`args = ["--from", "git+https://github.com/kawaii-snafy/yandex-tracker-mcp.git", "mcp-yandex-tracker"]`.

Restart Codex after editing the config.

### Claude Code

```sh
claude mcp add --transport stdio \
  --env YANDEX_TRACKER_TOKEN="..." \
  --env YANDEX_TRACKER_CLOUD_ORG_ID="..." \
  yandex-tracker \
  -- uvx mcp-yandex-tracker
```

Verify with `claude mcp list`, `claude mcp get yandex-tracker`, and `/mcp`
inside the session. For a non-cloud org swap in `YANDEX_TRACKER_ORG_ID`.

### Any MCP host

Point the host at the console script `mcp-yandex-tracker` (installed by the
package), or run it explicitly:

- `python -m yandex_tracker_mcp_server`
- `python run_server.py`

## Smoke test without a host

Pipe a raw request in and read the response back:

```sh
YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." \
  uvx mcp-yandex-tracker <<<'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

`tools/list` needs no credentials, so it is the safest first check — a healthy
server returns a JSON-RPC object listing the `tracker_*` tools. Any tool that
actually touches Tracker (e.g. `tracker_get_issue`) will exercise the token and
org id.

## Troubleshooting

| Symptom                                          | Likely cause                                                                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| Tool result with `isError: true`, "Set YANDEX_TRACKER_TOKEN…" | Token or org id missing from the host's env for this server.                 |
| `isError: true` with `Yandex Tracker API error <status>` | The SDK reached Tracker but got a non-2xx (auth, permissions, missing issue). |
| Host reports the server "crashed" or garbled     | Something wrote non-JSON to stdout. Only JSON-RPC may go to stdout.          |
| `isError: true`, "Install yandex_tracker_client…"| The runtime is missing the SDK dependency.                                   |
| JSON-RPC `error` with code `-32601`/unsupported method | The host called a method the server does not implement (see [ARCHITECTURE.md](ARCHITECTURE.md)). |

Errors from Tracker or from bad tool arguments come back **inside** a successful
`tools/call` response with `isError: true` — they are not JSON-RPC errors. Only
protocol-level problems (parse errors, malformed requests, unknown methods) use
the JSON-RPC `error` channel.
