#!/bin/sh
# Start the server with the command given as arguments, run the MCP handshake
# and tools/list over stdio, and fail unless the three dispatch tools answer.
# CI runs it against every way the server is installed: from git, from the
# release archive.
#
#   scripts/handshake.sh npx -y ./yandex-tracker-mcp.tgz
set -eu

out=$(mktemp)
{
  printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"ci","version":"1"}}}' \
    '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  # Keep stdin open: the server shuts down on EOF, often before it answers.
  sleep 5
} | "$@" > "$out"

node -e '
  const lines = require("fs").readFileSync(process.argv[1], "utf8").trim().split("\n").map(JSON.parse);
  const tools = lines.find((m) => m.id === 2).result.tools;
  if (tools.length !== 3) throw new Error(`expected 3 tools, got ${tools.length}`);
  console.log(tools.map((t) => t.name).join(", "));
' "$out"
