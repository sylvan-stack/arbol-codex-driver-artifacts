---
role: authored
spec: CDX-0
status: accepted
sources:
  - arbol-codex-driver:research/v1-driver-inventory.md
---
# Codex Driver · 00 Overview and legacy map

The Codex Driver is the Arbol 2 [Driver](../../arbol/GLOSSARY.md#driver) for the `codex` command-line tool. This specification says what it is in one page and where every part of the version 1 code went: carried over, changed, moved to the caller or dropped. It matters because version 1 solved this route by taking the tool apart: it pinned one exact build, ran the tool's command executor as a second process behind a bridge of its own, and refused every approval question. Most of that answered problems a Driver-owned home and the tool's current protocol no longer pose.

## Scope

Covered: what this Driver is, its requirements beyond [DRV-0](../../arbol/driver-contract/00-overview-and-boundary.md), the fate of each part of version 1, what the installed tool offers that version 1 did not use.

Not covered: behaviour in detail. Each row of the legacy map names the specification that carries it.

## What this Driver is

- One command-line program, `arbol-codex-driver`, written in TypeScript. Its command line is its only interface, and Arbol holds none of its code (DRV-0).
- It serves one vendor family, `chatgpt` ([CDX-1](01-subscriptions.md)).
- Every Subscription has its own home for the tool. Account operations and inference runs both go through `codex app-server`, started in that home and spoken to over standard input and output.
- A run is given what it needs in the request: system prompt text, working folders, conversation, and the Subscription, model and effort where the caller names them. What is left out comes from the Driver's settings file.
- It has no socket, no launch job, no database connection and no knowledge of Chat Sessions, routes or repositories.

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-0.1 | find the `codex` executable from `toolPath` in its settings file or else on the search path, read its version by running it, and report both | DRV-0.6 | Changed | `base.info`, `base.tool-cache`, `base.tool-missing`, `base.tool-old`, `probe.base-info` (codex-cli 0.159.2 on 7 October 2026; zero prompts) |
| CDX-0.2 | work with every tool version from the oldest supported one upward, and judge compatibility by the tool's answers, never by the size or checksum of one build | DRV-0.6 | Changed | `base.tool-old` (version boundary and later versions, no binary pin) |
| CDX-0.3 | need nothing but the tool and its state directory to start: no database, no other Arbol service, no file from an Artifact Corpus | DRV-0.8 | Changed | `C32` (info), `base.packaged-info`, `C10`, `run.lifecycle`, `live.run` (isolated base and fresh-run executable; continuity and complete lifecycle coverage pending) |
| CDX-0.4 | take the system prompt as text in the request and add nothing to it | DRV-0.2 | Changed | `C10`, `run.request`, `run.lifecycle` (system prompt passed unchanged as developerInstructions) |
| CDX-0.5 | use a request the tool marks as experimental only where a specification names it and says why | DRV-0.6 | New | `probe.run-protocol`, `run.lifecycle`, `run.images` (stable-schema fresh-run requests; native continuity and owner tools pending SYL-88/SYL-90) |

## Legacy map

Fate is one of: **Kept** (same behaviour, rewritten), **Changed** (same purpose, different behaviour), **Caller** (the purpose remains and belongs to the Driver's caller), **Dropped**.

### Process, transport and recovery

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| `__main__.py`, launch job `com.arbol.driver.codex`, socket `driver.codex.sock` | One resident process, framed JSON over a Unix socket | Dropped | DRV-0 |
| Build, instance and generation identity; admission sealing; retirement | Ran old and new Driver builds side by side during an upgrade | Dropped | DRV-0 |
| Dispatcher grants, attempt authority, launch receipts | Proved for every command and every published event that the caller still owned the turn | Dropped | DRV-0 |
| `state_main.py` and the state receiver | Second receiver for the state runtime | Dropped | none |
| `turn.execute`, `turn.cancel`, the `turn.events` stream | Start, stop and observe one turn | Changed: the run operations of the contract | DRV-2, CDX-2 |
| `turn.inventory`, `turn.describe`, `turn.attach`, `turn.ack`; the in-memory replay buffer | Let a restarted Root find running turns and replay their events | Caller | DRV-D2 |
| `manifest.json`: default for the transport, failover target, recovery seconds | Route properties declared by the installation | Caller | none |

### Starting the tool

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| `executor.resolve_executable` and the identity checks | Accepted exactly one build of the tool, by file size and SHA-256, and one layout of its helper program. Any update of the tool failed every turn until the Driver was rebuilt | Dropped | CDX-0.2 |
| `session.control_argv` | Started `codex app-server` with 27 features switched off, 2 switched on and notification commands cleared, as command-line overrides | Dropped. Decided 6 October 2026 (DRV-D26): the features stay as the tool ships them. The Driver writes only housekeeping settings into the configuration of the Subscription's home | CDX-1.5, CDX-3 |
| `session.validate_config` and the start refusals | Refused a turn when the Leather Bag's own configuration held anything Arbol could not represent: another model provider, a permission or network profile, saved environments, a start-up override file | Dropped. In a home the Driver writes, there is no foreign configuration to refuse | CDX-1.5 |
| The turn environment | The service's whole environment passed through, with two folders added to the search path | Changed: an allow-list | CDX-1.4 |
| A second process per turn: `codex exec-server`, the tool's own helper that carries out shell commands and file operations, started by Arbol and reached through Arbol's own bridge (`executor.py`, `tool_process.py`). It is a part of the `codex` tool and unrelated to the retired `universe` route | Made Arbol, instead of the app-server, the owner of the process that runs the agent's commands, and filtered every request between the two. Depends on requests the tool lists only as experimental, and accepted one version of the tool only | Dropped. Decided 5 October 2026 (CDX-D8): the app-server runs its tools itself, as it does for anyone who uses `codex` | CDX-3 |
| `system_prompt.py` and the instruction templates | Built the system prompt from template files in the Artifact Corpus | Caller. The Driver receives the finished text | CDX-0.4 |
| Default model `gpt-5.5` when none is named | Fixed fallback | Dropped. The model comes from the request or from the settings file, never from the Driver's code | DRV-0.2 |
| The seven thinking levels mapped to four efforts | `xhigh`, `max` and `ultra` all became `xhigh` | Dropped. The caller names an effort from the model catalog | DRV-1.21, CDX-2 |
| Fast mode | Accepted and ignored | Changed: a service tier where the catalog lists one for the model | CDX-2 |

### Conversation

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| A new thread for every attempt, never resumed | The whole earlier conversation was sent again as one block of text inside the first input, after the system prompt. Tool calls and reasoning of earlier turns were not in it | Changed, following the Product Specification's default: Arbol's history stays the authority; the tool's own thread is resumed when it exists and matches that history, and rebuilt from the history otherwise, with the run saying which happened | CDX-2 |
| System prompt placed in the user's input | The tool's instruction fields were not used | Changed: passed as instructions | CDX-2 |
| `images.py` | Wrote image attachments to a temporary folder and passed them as local images. All images of earlier messages were attached again on every turn | Kept for the current message; earlier images are sent again only when the thread is rebuilt | CDX-2 |

<!-- sources:
arbol:product-spec/12-lessons-and-invariants.md#Decisions for the successor's design
-->

### Reading the tool's output

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| `app_server.exec_events` and `protocol.map_exec_event` | Rewrote each app-server notification into the record shape of the tool's retired non-interactive mode, then mapped that | Changed: notifications are mapped directly | CDX-2 |
| Text and reasoning only at the end of each item | No partial output; command output only when the command had finished | Changed: the tool's delta notifications are used | CDX-2 |
| Usage | Last input and output counts only; cached and reasoning counts dropped; the model reported was the one asked for, also after the tool rerouted | Changed | CDX-2 |
| File-change summary | Expected another shape than the tool sends and printed the raw list, diffs included | Changed | CDX-2 |
| `notification_spool.py` | A queue between reader and consumer that could grow on disk without limit | Dropped | none |
| `protocol.build_argv` and the sandbox helpers | The retired non-interactive route; called only by tests | Dropped | none |

### Tools and permissions

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| Approval policy "never", full access, network on | Fixed for every turn. The route's "Full permissions" setting had no effect either way | Kept. Decided 6 October 2026 (DRV-D12): every run with tools is unrestricted, and the setting that had no effect is gone | CDX-3 |
| Approval requests from the tool | Never shown to anyone: declined, answered with an empty grant, or rejected as unsupported | Changed: none is expected. A command or file-change approval that arrives nonetheless is accepted, and any other request is answered with an error | DRV-3, CDX-3 |
| The feature profile and switched-off MCP servers | A fixed, known set of tools: shell and files | Dropped. Decided 6 October 2026 (DRV-D26): no part of the tool is switched off | CDX-3 |
| Commands that outlive the turn | Processes the executor started were left running on purpose when a turn ended or was cancelled | Dropped. Decided 5 October 2026 (DRV-D20): nothing a run started outlives it, on either Driver | DRV-0.10, DRV-2.19, CDX-2.16 |

### Failures and limits

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| `rate_limit.py`: wording match | Classified a failure by phrases anywhere in its text, rate limit first, so a login failure mentioning a quota became a rate limit. The tool's structured error information and its rate-limit notifications were not read | Changed: structured information first, wording as the fallback | CDX-4 |
| Login failure by wording, with the hint to run the tool's login | No flag, no state change | Changed: one typed error, and the Subscription moves to `needs_attention` | DRV-1.7, CDX-4 |
| "Requires a newer version" hint | Told the Leather Bag to update the tool or pick another model; the version shown was always "unknown" | Kept as a typed error naming the installed version | CDX-4 |
| Two shapes of a failed turn | A failure reported by the tool closed the turn one way, a failure of the connection another | Changed: one terminal shape | DRV-2 |
| No time limit for a turn | A silent turn held its processes until cancelled | Changed: limits are settings of the request | CDX-4 |
| Cancel | Ended the app-server without asking the tool to stop the turn | Changed: `turn/interrupt` first, then the process | CDX-2 |

### Account code that lived outside the Driver

| Version 1 part | What it did | Fate | Specified in |
|---|---|---|---|
| `universe_import.py` | Copied the tool's login file into Arbol's Keychain | Dropped | CDX-D2 |
| `universe_usage.py` | Read usage from the ChatGPT backend with the copied token | Dropped: `account/rateLimits/read` | CDX-1.11 |
| `provider_models.py`: ChatGPT list | Read the model list from the ChatGPT backend, reporting a client version | Dropped: `model/list` | CDX-1.12 |
| `drivers/universe`, `universe_wire.py`, `universe_auth.py`, fixed network addresses | The direct ChatGPT backend route | Dropped with the retired route | none |
| `completion.py`, ChatGPT branch | One-shot prompts sent straight to the backend | Changed: a run without tools through the tool | CDX-2 |
| `rate_limit_tracker.py`, route selection | Cooldown per route, choice of route per turn | Caller | none |

## What the installed tool offers

Compared on 5 October 2026 with `codex-cli` 0.159.2. Nothing version 1 passes has disappeared, and the file sizes and checksums version 1 pins are those of this build.

| Version 1 does | The tool's protocol offers |
|---|---|
| Nothing about accounts | `account/read`, `account/login/start`, `account/logout`, `account/rateLimits/read`, `model/list` |
| A new thread per attempt | `thread/resume`, `thread/fork`, `thread/read` |
| Text at the end of each item | `item/agentMessage/delta`, reasoning deltas, `item/commandExecution/outputDelta` |
| Kills the process to cancel | `turn/interrupt` |
| Declines every approval | Decisions `accept`, `acceptForSession`, `decline`, `cancel` for commands and file changes; `item/tool/requestUserInput` for questions |
| System prompt inside the input | `baseInstructions` and `developerInstructions` on `thread/start` |
| Ignores fast mode | `serviceTier` on `thread/start` and `turn/start`; service tiers listed per model |
| Classifies failures by wording | `codexErrorInfo` on error notifications; `account/rateLimits/updated` |
| Its own executor through `environment/add` | That request exists only in the experimental part of the protocol |

The app-server itself is marked experimental by the tool. CDX-2 to CDX-4 are written against its generated schema and probes of the installed tool, and CDX-0.2 exists because that schema can change between versions.

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D13 | How does the base query the installed tool without using the owner's setup or leaving a child behind? | Run `codex --version` in a private temporary home with `HOME` and `CODEX_HOME` replaced and the short environment allow-list. Cache the stated version by path, size and modification time. The query has a 10-second bound; on cancellation, timeout or the query process ending, end its process group before removing the temporary home. No prompt or account is needed. Carry over the Claude Driver's CLI, settings, error, state and Build identity design wherever the contract is the same; neither Driver imports the other at run time | Decided 7 October 2026 during SYL-79, a technical choice. A synthetic version command ignoring SIGTERM showed that the ordinary Node abort mechanism alone could leave the invocation waiting |

## Tests as evidence

The version 1 unit tests pin the behaviours of this route: the order of events for success, rate limit and failure, the refusal texts, the image handling, the bridge's filtering. They are listed with what each pins in the [inventory](../research/v1-driver-inventory.md#13-tests-as-evidence). Many pin parts that are dropped here; those marked Kept or Changed in the map are the starting point for this Driver's test cases.
