# Documentation

Yandex Tracker MCP is a dependency-light **stdio MCP server** that exposes
Yandex Tracker issues to LLM agents through the official
`yandex_tracker_client` SDK.

Pick the doc that matches what you are doing:

| You are…                                              | Read                             |
| ----------------------------------------------------- | -------------------------------- |
| **Connecting** the server to Codex / Claude Code / another MCP host | [INTEGRATION.md](INTEGRATION.md) |
| **Calling** the tools and want the exact arguments    | [TOOLS.md](TOOLS.md)             |
| **Understanding** how the server works internally     | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Extending / scaling** it (new tools, new behavior)  | [EXTENDING.md](EXTENDING.md)     |

The project [README](../README.md) has the quick-start; these docs go deeper.

## One-paragraph mental model

The server reads newline-delimited JSON-RPC 2.0 from stdin and writes
responses to stdout — **stdout carries only protocol messages, never logs**.
`server.py` speaks MCP (tool schemas, dispatch, error mapping); `client.py`
wraps the official SDK and serializes SDK objects to plain JSON. A fresh
`YandexTrackerClient` is built per tool call from environment variables. All
nine tools are named `tracker_*`.
