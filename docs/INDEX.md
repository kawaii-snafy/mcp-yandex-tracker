# Documentation

Yandex Tracker MCP is a **stdio MCP server** that exposes the Yandex Tracker REST
API v3 to LLM agents. It is built on the official MCP TypeScript SDK
(`@modelcontextprotocol/server`) and reaches Tracker with plain `fetch` calls
against documented v3 endpoints — one tool per endpoint, the API's own parameter
names in, the API's own JSON out. Those 179 endpoints reach a host as **three**
MCP tools rather than 179: a catalogue (`tracker_api`) and two dispatchers
(`tracker_read`, `tracker_call`).

Pick the doc that matches what you are doing:

| You are…                                                            | Read                               |
| ------------------------------------------------------------------- | ---------------------------------- |
| **Connecting** the server to Codex / Claude Code / another MCP host | [INTEGRATION.md](INTEGRATION.md)   |
| **Calling** an endpoint and want the exact arguments                | [TOOLS.md](TOOLS.md)               |
| **Understanding** how the server works internally                   | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Extending / scaling** it (new tools, new behavior)                | [EXTENDING.md](EXTENDING.md)       |

The project [README](../README.md) has the quick-start; these docs go deeper.

## One-paragraph mental model

`@modelcontextprotocol/server` owns the JSON-RPC 2.0 stdio transport, lifecycle,
and `tools/list` / `tools/call` routing — **stdout carries only protocol
messages, logs go to stderr**. `src/client.ts` holds the whole Tracker side:
config from the environment and a single `Tracker.request()` that builds a `/v3`
URL, throws `TrackerApiError` on a bad response, and returns the decoded body
untouched. Every endpoint in `src/tools/` is one entry in an array — name,
description, a Zod shape for the documented parameters, and a `run` that calls
`request()` — so the registry _is_ the API surface. `src/dispatch.ts` projects
that registry into the three tools a host sees: `tracker_api` carries the
catalogue and hands out argument schemas, `tracker_read` and `tracker_call` run
the endpoints. A few read-only `tracker://` **resources** (the catalogue, an issue
snapshot, the reference dictionaries) sit alongside for `@`-mention context.

## The rule everything else follows

The [official documentation](https://yandex.ru/support/tracker/en/llms.txt) is
the only source of truth for Tracker. Every page is markdown by appending `.md`,
and every tool's description links to the page it was written from.
