---
role: authored
---
# Live check: the agent's shell sees the Arbol chat identity · 11 November 2026

SYL-399 qualifies CDX-2.22 and DRV-2.37 at the real tool boundary. This record holds tools-on messages through the Codex Driver on the test Subscription `test-chatgpt`.

**Result: passed through installed Build `b`.** The agent's own shell printed the request's `rootId` and `chatSessionId`, not the stale values in the caller's environment, and did not see an unrelated caller variable. The reported output matched the expected line after the verified redaction transform, not as an unmasked equality; see "Redaction finding".

## What ran

| Item | Value |
|---|---|
| Driver | Installed Build `b`, source `arbol-codex-driver@e23ea80` (SYL-207 code `c13452a` and the SYL-399 static-baseline repair included) |
| Tool | codex-cli 0.162.1 at `/opt/homebrew/bin/codex` |
| Subscription | `test-chatgpt`, in the test state directory `~/Library/Application Support/Arbol/drivers/arbol-codex-driver` |
| Model and effort | the Driver's default model, effort `low` |
| Caller environment | Clean: `HOME`, `USER`, `LOGNAME`, `SHELL`, `PATH` (with `/opt/homebrew/bin`), `LANG`, plus stale `ARBOL_ROOT=stale`, `ARBOL_CHAT=0f0e0d0c-0b0a-4908-8706-050403020100` and the unrelated `SYL399_UNRELATED=caller` |
| Request | `tools: "all"`, `rootId: "qualify399"`, `chatSessionId: "4106e8fc-e03b-4c65-a2b0-30a21a0d6d72"`, empty history |
| Message | "Run this exact shell command with your shell tool and reply with its output only, nothing else: `echo "$ARBOL_ROOT $ARBOL_CHAT ${SYL399_UNRELATED:-unset}"`" |

Usage before: weekly window 32 %, read through the Driver just before the first attempt. Build `b`'s own build check confirmed the window was open before this run. Spent: 44,979 input tokens (34,560 cached) and 85 output tokens.

## What the Driver reported

| Event | Content |
|---|---|
| `tool_started` | `shell`, command `echo "$ARBOL_ROOT $ARBOL_CHAT ${SYL399_UNRELATED:-unset}"` |
| `tool_finished` | `ok: true`, `exitCode: 0`; output matched the expected line after the verified redaction transform |
| `text` | matched the same expected line after the same transform |
| `finished` | `completed`, exit status 0 |

The expected line is `qualify399 4106e8fc-e03b-4c65-a2b0-30a21a0d6d72 unset`. The Driver masks configured private values in run output (see "Redaction finding"), so this is not an unmasked equality check. The check applied that same masking to the expected line, using the Driver's own `diagnostic_values` and `safe_text`, and compared the result with the reported output: they are identical, with no other character changed. The values themselves are not recorded here.

## Earlier attempt, from the source checkout

Before Build `b` existed, one message ran from the source checkout at `bff5577` (`driverBuild` `0`) with the same request shape and chat `a0999402-a718-4cfb-a64b-d3edebd1a729`. Codex answered only "timed out negotiating with the code-mode host" and ran no tool, so that attempt proves nothing either way. It spent 67,518 input tokens (46,976 cached) and 113 output tokens.

## Redaction finding

With `tools: "all"`, `run.py` collects every string in the `mcp_servers` table of the owner's Codex configuration through `owner_setup.diagnostic_values`. The Driver then replaces each of those strings wherever it appears in run events, through `safe_text`. Nothing sets a minimum length, so a short configured string also matches inside unrelated text. For example, if the configuration held the synthetic value `ab`, a tool output `cab ab` would be reported as `c[redacted] [redacted]`. Event fields, call identifiers, the agent's text and tool output are all affected. `sanitize_diagnostic` says a tool's input and output keep their vendor shape, but here the tool output is scrubbed. Runs without tools, such as `dev build-check`, are not affected. This predates SYL-207 and SYL-399; it is recorded for the Arc Review as a separate fix.

## How to repeat it

Write a request file like the one above with a fresh UUID. Then run:

```sh
env -i HOME="$HOME" USER="$USER" LOGNAME="$USER" SHELL=/bin/zsh \
  PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin" LANG=en_US.UTF-8 \
  ARBOL_ROOT=stale ARBOL_CHAT=0f0e0d0c-0b0a-4908-8706-050403020100 SYL399_UNRELATED=caller \
  arbol-codex-driver --state-dir "$HOME/Library/Application Support/Arbol/drivers/arbol-codex-driver" \
  run --request request.json
```

It passes when the `shell` call's output is `<rootId> <chatSessionId> unset`. It spends one small message, so run it only when asked (DRV-5.4).
