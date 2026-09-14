# Yandex Tracker MCP

A stdio MCP server that puts the whole [Yandex Tracker REST API
v3](https://yandex.ru/support/tracker/en/llms.txt) in front of an LLM agent —
issues, comments, checklists, attachments, worklog, links and transitions; bulk
operations and imports from another tracker; queues, macros, local fields,
workflows, triggers and components; boards, columns and sprints; projects,
portfolios and goals; saved filters, dashboards, absences, users and the
reference dictionaries.

It is a thin wrapper on purpose: **one tool per documented endpoint**, the API's
own parameter names on the way in, the API's own JSON on the way out. Every
tool's description links to the documentation page it was written from, so the
agent can always read the source of truth.

## Usage with Codex

Add the server to `~/.codex/config.toml`:

```toml
[mcp_servers.yandex-tracker]
command = "npx"
args = ["-y", "mcp-yandex-tracker"]

[mcp_servers.yandex-tracker.env]
YANDEX_TRACKER_TOKEN = "..."
YANDEX_TRACKER_CLOUD_ORG_ID = "..."
```

To run from a clone instead, build it (`npm run build`) and point the host at
the entry point:

```toml
command = "node"
args = ["/path/to/mcp-yandex-tracker/build/cli.js"]
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
  -- npx -y mcp-yandex-tracker
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
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  sleep 5
} | YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." npx -y mcp-yandex-tracker
```

The trailing `sleep` keeps stdin open: `printf` alone closes it immediately and
the server shuts down on EOF, often before it has answered `tools/list` — you
then get only the `initialize` reply.

The second response line should be a JSON-RPC object with `tracker_*` tools. The
server is stdio-only, so stdout is reserved for MCP JSON-RPC messages (logs go
to stderr).

## Documentation

Deeper docs live in [`docs/`](docs/INDEX.md):

- [INTEGRATION.md](docs/INTEGRATION.md) — connect the server to a host.
- [TOOLS.md](docs/TOOLS.md) — every tool, its endpoint, and its doc page.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the server works internally.
- [EXTENDING.md](docs/EXTENDING.md) — add tools, rules, and scaling notes.

## Development

```sh
git clone git@github.com:kawaii-snafy/mcp-yandex-tracker.git
cd mcp-yandex-tracker
npm install

npm run typecheck   # tsc --noEmit — Node strips the types without checking them
npm run build       # tsc → build/, then chmod +x build/cli.js
npm run lint        # eslint
npm run format      # prettier --write
npm run docs:tools  # regenerate the docs/TOOLS.md tables

node src/cli.ts     # run from source
node build/cli.js   # run the compiled entry point
```

Node runs the TypeScript sources directly, so development needs Node 22.18 or
newer. **The published package does not**: `build/` is plain JavaScript and
`build/cli.js` carries a `#!/usr/bin/env node` shebang, so `npx` works on a
machine with only Node 20+.
