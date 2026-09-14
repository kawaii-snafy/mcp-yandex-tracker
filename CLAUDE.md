# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **stdio MCP server** that exposes the Yandex Tracker REST API v3 to LLM agents.
It is a deliberately thin wrapper: **one tool per documented endpoint**, the API's
own parameter names on the way in, the API's own JSON on the way out. TypeScript
on Node, compiled by `tsc` into plain JavaScript under `build/`, published to
npm. There is no HTTP/SSE transport — one process serves one client over
stdin/stdout.

## The rule that governs every other decision

**The official documentation is the only source of truth for Yandex Tracker.**

- Index of every page: <https://yandex.ru/support/tracker/en/llms.txt>
- Any page is markdown by appending `.md`:
  `https://yandex.ru/support/tracker/en/api/<section>/<page>.md`

Blogs, Stack Overflow, observed production behavior, and model memory are **not**
sources. A path, parameter or field that is not on a page from `llms.txt` does
not go into the code. Before touching a tool, open its page — every tool's
description links to it. If something is genuinely needed and genuinely
undocumented, that is a deviation: record it in `docs/TOOLS.md` with the reason.

## Commands

```sh
npm install

npm run typecheck            # tsc --noEmit — Node strips the types, it does not check them
npm run build                # the same tsc with emit: src/ -> build/, then chmod +x
npm run lint                 # eslint
npm run format               # prettier --write
npm run docs:tools           # regenerate the docs/TOOLS.md tables

node src/cli.ts              # run from source
node build/cli.js            # run the shipped artifact
```

Node runs the TypeScript sources directly by stripping the types, which needs
Node 22.18 or newer for development; the compiled `build/` still runs on Node 20.

There is no test suite: `npm run typecheck` (or `npm run build`) plus the
smoke-test below is what validates a change.

Smoke-test without a host — MCP requires the `initialize` handshake before any
other request, so send it (and the `initialized` notification) first:

```sh
{ printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  sleep 5
} | YANDEX_TRACKER_TOKEN="..." YANDEX_TRACKER_CLOUD_ORG_ID="..." node build/cli.js
```

The trailing `sleep` keeps stdin open: `printf` alone closes it immediately and
the server shuts down on EOF, often before it has answered `tools/list`.

## Environment

`YANDEX_TRACKER_TOKEN` plus exactly one org id (`YANDEX_TRACKER_CLOUD_ORG_ID`
for cloud orgs, or `YANDEX_TRACKER_ORG_ID`) are required; a missing one surfaces
as a clean tool error, not a crash. Optional: `YANDEX_TRACKER_AUTH_SCHEME`
(`OAuth` default, `Bearer` for IAM tokens), `YANDEX_TRACKER_BASE_URL` (host only
— the client always appends `/v3`), `YANDEX_TRACKER_TIMEOUT` (seconds).

## Architecture

```
src/
  cli.ts       # serveStdio(() => buildServer())
  server.ts    # buildServer(): registers every tool and resource; getTracker()
  client.ts    # config, errors, Tracker over fetch — the whole Tracker side
  tool.ts      # the ToolDef type and the tool() helper
  resources.ts # the read-only tracker:// surface
  tools/       # issues.ts bulkchange.ts imports.ts filters.ts queues.ts
               # macros.ts boards.ts entities.ts projects.ts dashboards.ts
               # gaps.ts admin.ts users.ts
```

Tool modules mirror the sections of the documentation, so a doc page maps to
exactly one code file. `src/tools/index.ts` concatenates them into `allTools`.

`tsconfig.json` covers `src` only — it is both the type checker and the build,
and `rootDir`/`outDir` make `build/` mirror `src/`. Relative imports keep their
`.ts` extension so Node can run the sources directly; `rewriteRelativeImportExtensions`
turns them into `.js` on emit. `scripts/gen-tools-doc.ts` is outside that config
and is therefore not type-checked — it is a dev utility, run by Node directly.

Four cross-cutting mechanisms to know before editing:

- **Tools are data.** Each is a `tool({ name, description, input, run })` entry.
  `input` is a Zod shape; `tool()` infers the type of `run`'s `args` from it, so
  nothing is annotated by hand. The registry is read by `buildServer` and by
  `scripts/gen-tools-doc.ts` alike.
- **The description is a contract.** Summary line, blank line,
  `<METHOD> /v3/<path>`, then the documentation URL. `tool()` reads the method
  back out of it to derive the tool's `effect` — `read`, `create` or `modify` —
  which `buildServer` turns into the MCP annotations (`readOnlyHint` /
  `destructiveHint`) a host uses to decide whether to ask the user. Twenty tools
  whose method misleads declare `effect` themselves. Nothing checks that the
  stated endpoint is the one `run` actually calls, so keep them in step by hand.
- **`Tracker.request(method, path, { params, body, headers })`** is the only way
  out. It builds `{baseUrl}/v3{path}`, retries 429/5xx on idempotent methods,
  maps a transport failure to `TrackerApiError(0, …)` and any non-2xx to
  `TrackerApiError(status, …)`, and returns the decoded body **untouched**.
  `upload()` and `download()` are the two variants the wire format forces.
- **Errors are thrown, not wrapped.** `@modelcontextprotocol/server` turns a
  thrown error into an `isError: true` tool result carrying its message, so no
  handler needs a try/catch.

## Non-negotiable rules

- **Documentation first** — the rule above. No undocumented endpoints, no guessed
  parameters.
- **One tool per endpoint, nothing in between.** No projections, no renaming, no
  client-side pagination, no convenience tools that compose several calls. If a
  response is too big, trim it with the API's own `fields` / `expand`.
- **No second HTTP path.** All Tracker access goes through `Tracker.request()`.
  Imports stay at `@modelcontextprotocol/server` + `zod` — the only two
  `dependencies`, and there is no bundler, so a third one is a third thing every
  user downloads.
- **No `any`, no `as`.** The single cast in the project lives in `src/tool.ts`
  and is explained there.
- **stdout is protocol-only.** Never write to stdout — it corrupts the MCP stream.
- **Keep `docs/TOOLS.md` in sync**: `npm run docs:tools` after changing a tool.

## Adding a tool

Find the endpoint's page in `llms.txt`, read the `.md`, and add one `tool({...})`
entry to the matching `src/tools/` array — description as summary, blank line,
`<METHOD> /v3/<path>`, page URL. Then `npm run docs:tools`. See
`docs/EXTENDING.md` for the full pattern and the naming conventions.

## Further docs

`docs/` has the deep guides: `ARCHITECTURE.md` (internals), `EXTENDING.md`
(adding tools, scaling), `TOOLS.md` (the generated tool index), and
`INTEGRATION.md` (connecting hosts). `AGENTS.md` mirrors the rules above.
