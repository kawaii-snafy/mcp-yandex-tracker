# Documentation

Yandex Tracker MCP is a **stdio MCP server** that exposes Yandex Tracker issues
to LLM agents. It is built on the official MCP Python SDK (`FastMCP`) and reaches
Tracker through the official `yandex_tracker_client` SDK.

Pick the doc that matches what you are doing:

| You are…                                              | Read                             |
| ----------------------------------------------------- | -------------------------------- |
| **Connecting** the server to Codex / Claude Code / another MCP host | [INTEGRATION.md](INTEGRATION.md) |
| **Calling** the tools and want the exact arguments    | [TOOLS.md](TOOLS.md)             |
| **Understanding** how the server works internally     | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Extending / scaling** it (new tools, new behavior)  | [EXTENDING.md](EXTENDING.md)     |

The project [README](../README.md) has the quick-start; these docs go deeper.

## One-paragraph mental model

`FastMCP` (the official MCP SDK) owns the JSON-RPC 2.0 stdio transport,
lifecycle, and `tools/list` / `tools/call` routing — **stdout carries only
protocol messages, logs go to stderr**. Everything lives in one module,
`mcp_yandex_tracker.py`, split into two commented sections: an **MCP server
layer** (the `@tool`-decorated typed functions and a cached
`YandexTrackerClient`) and an **SDK client layer** (wraps the Tracker SDK and
serializes SDK objects to plain compact JSON). The client is built once
(lazily) from environment variables and reused. All tools are named `tracker_*`.
