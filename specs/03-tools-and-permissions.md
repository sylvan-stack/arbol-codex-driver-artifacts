---
role: authored
spec: CDX-3
status: accepted
---
# Codex Driver · 03 Tools and permissions

How the Codex Driver meets [DRV-3](../../arbol/driver-contract/03-tools-and-permissions.md): how the `codex` tool is started so that the agent works unrestricted, with the owner's own skills and MCP servers, with nothing of the tool switched off but its memories, and with nothing asking for permission, and what a run without tools is on a tool that cannot be started without its tools. It matters because the tool's two settings, sandbox and approval policy, combine in ways that are easy to get wrong: one combination refuses silently.

Everything stated about the installed tool was observed on 5 October 2026 with `codex-cli` 0.159.2 and is recorded in the [probe record](../research/tool-probes-2026-10-05.md).

## Scope

Covered: the parts of the tool, of which the Driver switches off only its memories; the owner's own skills and MCP servers; the settings that make a run unrestricted; a request of the tool that arrives nonetheless; sub-agents; the run without tools; what this Driver cannot carry.

Not covered: the contract (DRV-3); the process, threads and events of a run (CDX-2).

## Behaviour

### Tools, and nothing switched off but memory

The tool's own two capabilities are always there: running shell commands, which is `shell` in contract terms, and changing files by patch, `apply_patch`. The app-server runs them itself; there is no separate executor process.

Beyond them the Driver switches one part of the tool off: its own memories, with the feature switch `memories = false` in the home's configuration (DRV-3.25). It writes no other feature switch, so every other part is as the tool ships it.

| Part of the tool | State | How |
|---|---|---|
| `shell`, `apply_patch` | On | Built in |
| Web search | On | The configuration key `web_search`, set to `live` |
| Sub-agents, plug-ins and the applications connected to the account, the MCP servers the tool adds for them, image generation, browser and computer use, hooks, skill search, tool suggestions, goals | On | As the tool ships them |
| The tool's own memories | Off | The feature switch `memories`, written as `false` |
| Whatever else the tool itself ships switched off | Off | As the tool ships it. The Driver switches nothing on |

The Driver's configuration file keeps two settings that are housekeeping and no concern of the agent: the check for updates and analytics are off (CDX-2).

Observed with the installed tool: `codex features list` shows 152 features, 43 of them stable and on. Four are stable and off as shipped, among them `memories`. A fresh home with plug-ins on clones a plug-in catalogue of 88 MB at its first start, and the tool adds two MCP servers by itself. Without the separate executor, commands and patches ran inside the app-server process. Asked for its tools on 6 October 2026 in the signed-in test account, the model named, among others, `exec_command` and `exec` for commands, `apply_patch`, `write_stdin`, a web tool, six tools for sub-agents (`spawn_agent`, `wait_agent`, `send_message`, `interrupt_agent`, `list_agents`, `followup_task`), two for asking the person, and tools for goals, pictures and MCP resources. A web search it then made arrived as an item `webSearch` with its query.

Observed on 6 October 2026, without a login: with nothing switched off the tool answered its first request 0.01 to 0.04 seconds after its start and had started a thread after 0.03 to 0.06 seconds, the same as with the switched-off configuration of earlier drafts. Only the first start in a new home differed: 0.2 seconds, and within 25 seconds the home had grown to 91 MB. A folder's `AGENTS.md` was named among the instruction sources of a thread started there; a folder holding only a `CLAUDE.md` gave none.

Observed in version 1: 27 features switched off and 2 switched on by command-line overrides, every saved MCP server disabled per thread, and a separate executor process behind a bridge that filtered each request. The executor was `codex exec-server`, a part of the tool itself: Arbol started one per turn and told the app-server, with the experimental request `environment/add`, to send its commands and file operations there.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/session.py#control_argv
arbol:drivers/codex/arbol_driver_codex/session.py#validate_config
arbol:drivers/codex/arbol_driver_codex/executor.py
-->

### The owner's own skills and MCP servers

A run with tools has the skills and the MCP servers the owner set up for `codex` (DRV-3.31).

| What | Where the owner keeps it | How a run gets it |
|---|---|---|
| Skills | The folder `~/.agents/skills` | The tool finds that folder by itself, whatever its home |
| MCP servers | The tables `[mcp_servers]` in the file `~/.codex/config.toml` | The Driver reads those tables when a run starts and hands them to the tool in the `config` of `thread/start` or `thread/resume`. They are written nowhere |

The tables can hold secrets of the owner's, such as a key in a server's environment. The Driver passes the tables on as they are and never writes, logs or reports them (DRV-0.3). Nothing else of the owner's own `~/.codex` reaches a run: no other setting of that file, and not the login. A missing configuration file or missing tables means there are no owner servers. An unreadable or malformed file, a non-table `mcp_servers` value, or values that cannot be represented in JSON refuse the run with `invalid_input` and a fixed message containing no file contents or parser excerpt. Owner table strings are removed from every emitted event and text output, including tool inputs and results, vendor diagnostic messages and stderr excerpts. The event and result shapes stay the same; matching literal private values become `[redacted]`. Assistant history fingerprints use the redacted text delivered to the caller. The Driver does not read the tool’s credential files to discover additional values.

Observed with the installed tool on 6 October 2026: in a new home, with nothing linked, the tool listed 40 skills from the owner's `~/.agents/skills`. The owner's `~/.codex/skills` was empty. A server handed over in the `config` of `thread/start` was started, and the home's configuration file stayed as it was.

### Nothing asks for permission

Every run with tools gets the sandbox `danger-full-access` and the approval policy `never`. Both are sent when the thread is started and again with every turn. The tool then runs every command and applies every patch without a question and outside its sandbox: with the files, the programs and the network of the owner's account.

Observed with the installed tool on 6 October 2026, one real run under these settings: a command that writes a file in the working folder, one that writes a file outside it and one that fetches a web address all ran, and the tool sent no request to the client. `thread/start` reported the sandbox as `dangerFullAccess`.

Observed in version 1: the same two settings on every turn. The approval requests the tool still sent were declined, answered with an empty grant, or rejected as unsupported.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/session.py#tool_policy
arbol:drivers/codex/arbol_driver_codex/app_server.py
arbol:product-spec/06-tools-and-permissions.md#Defaults and remaining decisions
-->

### A request that arrives nonetheless

None is expected under these settings. Should the tool send one all the same, the Driver answers it at once and emits a `notice`.

| The tool asks | The Driver answers |
|---|---|
| `item/commandExecution/requestApproval`, `item/fileChange/requestApproval` | `accept` |
| Anything else: a request for extra permissions, a request to call a tool of the client, an MCP question, a question for the person | An error, so that it is never left open |

Observed with the installed tool: an unanswered request stayed open for 45 seconds without any notification.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/app_server.py
-->

### Sub-agents

The feature that lets the agent start sub-agents is on in the tool as shipped, and the Driver leaves it on. The agent starts one only when it is asked to: `thread/start` reports `multiAgentMode: "explicitRequestOnly"`.

| What happens | What the tool sends |
|---|---|
| The agent starts a sub-agent | On the run's thread: an item `subAgentActivity` of kind `started`, with the sub-agent's path and `agentThreadId`, the thread the sub-agent works on |
| The sub-agent works | Ordinary notifications that name the sub-agent's thread: `turn/started`, the items of its commands and messages, `turn/completed` |
| The agent waits | On the run's thread: an item `collabAgentToolCall` whose `tool` is `wait` |
| The sub-agent ends | On the run's thread: an item `subAgentActivity` of kind `completed` with the same `agentThreadId` |

The Driver turns this into the contract's events as follows. The `subAgentActivity` items of one sub-agent are one tool call named `spawn_agent`: `tool_started` at kind `started`, `tool_finished` at kind `completed`, with `agentThreadId` as the call's identifier. Every notification that names that thread becomes the event it would be on the run's own thread, with `parentCallId` set to that identifier, and its messages are no part of the answer (DRV-3.24). An item `collabAgentToolCall` is a tool call under the name in its `tool`. Where the agent waits for its sub-agent inside the turn, the turn's `turn/completed` is the end of the run. A sub-agent whose turn is still active when the run's turn completes is waited for (CDX-2, DRV-3.32). A sub-agent is stopped by a `turn/interrupt` for its own thread and turn; stopping the run's turn alone lets it work on (CDX-2).

A second form announces the child through an item `collabAgentToolCall` whose `tool` is `spawnAgent`. Its successfully completed item names the child thread in `receiverThreadIds`. The Driver keeps this as one tool call under the tool's name, `spawnAgent`, with the item's `id` as its call identifier; every event of that child has this identifier as `parentCallId`. That child is tracked for waiting and stopping in the same way as one announced by `subAgentActivity`. A child notification may precede the completed spawn item: while a known `spawnAgent` call is in progress, the Driver buffers foreign-thread notifications, then replays those matching its announced receiver threads. Unmatched notifications are passed over with one `notice`, as CDX-2 says.

Historical TypeScript live observation on 7 October 2026 during SYL-89, `codex-cli` 0.159.2 on `test-chatgpt`, `gpt-5.6-luna` at low effort: the spawn arrived as `collabAgentToolCall` of `tool` `spawnAgent`, first `inProgress` with no receiver thread and then `completed` with one `receiverThreadIds` entry and `agentsStates` of `pendingInit`. A notification of that child arrived before the completed spawn item. No `subAgentActivity` was reported by this run. The first stopping check missed the child and failed; its retained evidence is `research/stopping-initial-2026-10-07.json`. After the second form was supported, a focused live check stopped the main and child turns during the child's command in 55 ms and left none of the verified groups running; `research/stopping-subagent-2026-10-07.json` records that passing check.

Observed with the installed tool on 6 October 2026, one real run: the order above. The sub-agent ran its command on its own thread and ended with a message of the phase `final_answer`; the agent's messages on the run's thread carried the phases `commentary` and `final_answer`. Observed the same day, one real run: after the run's turn alone had been interrupted, the sub-agent finished its command and its turn, and the item of kind `completed` arrived on the run's thread although that thread's turn was over.

### A run without tools

The tool cannot be started without its shell and patch tools. For a request whose `tools` is `none` the Driver locks the run down instead: the sandbox `read-only`, the approval policy `never`, and, when the request names no working folder, an empty folder of its own.

Whatever the agent does in such a run is accepted, as the owner decided on 6 October 2026 (SYL-34). A command it runs is reported with `tool_started` and `tool_finished` like any other, and the run is not failed for it. The sandbox keeps a command from writing and from using the network. It does not keep a command from reading files elsewhere on the machine.

Observed with the installed tool under these settings: a shell command that only reads ran inside the sandbox; one that writes in the working folder was refused by the sandbox; a refused patch left no trace in the stream, neither a question nor a tool call, and only the agent learnt of the refusal.

### What this Driver does not carry

Questions from the agent to the person (DRV-3.26). The tool lets its agent ask only in a collaboration mode that needs the experimental part of its protocol, which this Driver does not use (CDX-0.5). In the default mode the agent's attempt to ask fails inside the tool and the agent is told so. A feature that would allow it in the default mode is under development in the installed version and off.

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-3.1 | run commands and patches through the app-server itself, without a separate executor process | DRV-3.20 | Changed | `C11`, `C35`; `MapperTools.test_patch_kinds_and_vendor_failure_leave_run_completed`; `live.tools` (single app-server; no separate executor) |
| CDX-3.2 | write `memories = false` and no other feature switch into the configuration of a home, so that every other part of the tool is as the tool ships it, and set `web_search` to `live` | DRV-3.25 | Changed | `C35`; `AppServerTests.test_private_home_configuration_clean_environment_and_owner_cleanup`; `probe.tools` (memories only, live web search and unchanged private configuration) |
| CDX-3.3 | send the sandbox `danger-full-access` and the approval policy `never` when the thread of a run with tools is started and with every turn | DRV-3.21 | Changed | `C11`, `C35`; `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread`; `live.tools` (inside/outside writes and network fetch, low effort, no questions) |
| CDX-3.9 | answer a command approval or a file-change approval that arrives nonetheless with `accept` and every other request of the tool with an error, and emit a `notice` | DRV-3.22 | Changed | `C25`, `C35`; `MapperTools.test_child_request_notice_without_turn_replays_after_spawn_discovery` (command/file accepts; other requests answered with errors and attributed notices) |
| CDX-3.11 | for a run without tools, send the sandbox `read-only` and the approval policy `never`, use an empty folder of its own when the request names no working folder, and report a tool call that occurs nonetheless without failing the run | DRV-2.20 | Changed | `C19`, `C35` (read-only/no network, scratch cleanup, unexpected tool call reported without failing); the real no-tools observation remains historical |
| CDX-3.12 | set `parentCallId` on every event that reports what a sub-agent did, and keep a sub-agent's text out of the answer: a sub-agent's work is every notification that names a thread announced by a `subAgentActivity` item or by the `receiverThreadIds` of a successfully completed `collabAgentToolCall` of tool `spawnAgent`; the parent identifier is the call that announced that thread | DRV-3.24 | New | `C35`; `MapperTools.test_child_post_turn_output_notices_and_retry_keep_parent_attribution`; `MapperTools.test_child_request_notice_without_turn_replays_after_spawn_discovery`; `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`; `live.tools` |
| CDX-3.13 | emit no question from the agent, for as long as the tool offers such questions only in its experimental mode | DRV-3.26 | Kept | `C25`, `C35` (vendor questions rejected, no ask events); Codex-scoped `C33` refuses unmatched control answers; experimental collaboration modes remain unused |
| CDX-3.14 | hand the `[mcp_servers]` tables of the owner's `~/.codex/config.toml` to the tool in the `config` of `thread/start` or `thread/resume` for a run with tools, and write, log and report them nowhere; read nothing else of the owner's `~/.codex` and write nothing there | DRV-3.31 | New | `C9`, `C37`; `OwnerSetup.test_preserves_mcp_tables_and_reads_no_other_owner_file`; `OwnerSetup.test_malformed_unreadable_and_non_json_tables_have_nonsecret_errors`; `OwnerDiagnostics.test_transient_owner_payload_keeps_exact_json_values_and_home_unmodified`; `ToolRuns.test_resume_forwards_changed_owner_mcp_in_memory_without_polluting_saved_state`; `probe.tools` (25 skills, three enabled owner servers, one disabled table, no owner metadata changes) |
| CDX-3.15 | keep a run going after its turn has completed while a sub-agent's turn is still active, and stop a sub-agent with a `turn/interrupt` for its own thread and turn | DRV-3.32 | New | `C15`, `C35`; `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`; `ToolRuns.test_late_noncommand_child_tool_closes_after_completed_turns_and_background_work`; `live.tools` (child and background completion); real stopping evidence remains historical |

CDX-3.4 to CDX-3.8 and CDX-3.10 described levels of asking and approval questions. They were withdrawn on 6 October 2026 with DRV-D12, and their numbers are not used again.

## Python migration verification on 7 October 2026

Current `Class.method` references identify the Python unittest methods in `tests/`. They cover the implemented shell/configuration baseline and the sub-agent attribution, waiting and interruption needed by stopping. The original scoped `C11`, `C19` and `C15` scenarios are retained, as are the limited Codex `C33` scenarios described in CDX-2. The scoped suites do not claim the advanced tool/owner-MCP scenarios reserved for SYL-90. Complete development/live checks and the first numbered Codex Build remain pending SYL-92/SYL-94, and SYL-91 error/limit work is now verified in CDX-4.

Evidence: `research/python-migration-2026-10-07/verification.json`, `research/python-migration-2026-10-07/packaged-unit.txt`, `research/python-migration-2026-10-07/scoped-conformance-runs.txt`, `research/python-migration-2026-10-07/scoped-conformance-stops.txt`, `research/python-migration-2026-10-07/compatibility.json`, `research/python-migration-2026-10-07/no-prompt-probes.json` and `research/python-migration-2026-10-07/standalone-rehearsal.json`. The standalone candidate and relocated copy use pinned CPython 3.14.8. No live inference was sent for SYL-95; the dated real sub-agent and sandbox observations below, including the failed first stopping attempt, remain historical evidence.

## SYL-90 verification, 7 October 2026

The Python Driver passes `C9`, `C25`, `C35` and `C37`, retaining the 29 original scoped scenario invocations. Focused `OwnerSetup`, `OwnerDiagnostics`, `MapperTools` and `ToolRuns` tests cover exact transient MCP values, diagnostic privacy, resumed owner setup, child requests and late tool completion. The no-prompt `probe.tools` in `scripts/check_tools.py` discovers 25 owner skills and all three enabled owner servers; all four tables, including the disabled one, are forwarded unchanged. It compares metadata across the whole owner trees and observes no changes. The startup notifications prove discovery; they do not claim that a server needing its own sign-in is authenticated.

The fresh Python `live.tools` uses `test-chatgpt`, `gpt-5.6-luna` at its lowest supported effort, `low`: inside/outside writes and a network fetch succeed without questions, child text stays out of the main answer, and the finite background command result arrives after the main answer. Both checks require explicit invocation and are excluded from the offline unit suite. Evidence is in `research/tools-2026-10-07/`. Earlier failed attempts and their causes are retained there; no failure is recast as passing. MCP sign-in remains outside this task. Complete error/limit behavior is verified by SYL-91 in CDX-4; development checks and a numbered Codex Build remain SYL-92 and SYL-94.

## Not established

- A sub-agent the agent does not wait for in a real completed run, and what `collabAgentToolCall` items other than `wait` and `spawnAgent` carry. Stopping an active child command was verified historically on 7 October 2026 by the TypeScript `live.stopping` check; current synthetic late-child waits are covered by `Lifecycle.test_main_completion_waits_for_late_child_and_closes_spawn_once`. SYL-90 now records a fresh Python live check of an ordinary completed child and background command in `live.tools`; a fresh real child-stop check remains separate.
- How long the first start in a new home takes for the caller, while the tool fetches its plug-in catalogue. Later starts in the signed-in test account answered `initialize` after 0.2 seconds and had a thread started after about one second more, most of it the account and model requests.
- Skills the owner keeps in `~/.codex/skills`. A link from the home to that folder works, but the tool then writes its five bundled skills into the owner's folder. The folder is empty today.
- How the owner signs an MCP server in for a Subscription's home, where a server needs that.
- Whether the shell and patch tools, web search and sub-agents can be taken away for one run. Until they can, the lock-down above is what a run without tools gets on this Driver.
- Whether the tool ever sends an approval request under `never`. Version 1 received some.
- How a request for extra permissions is granted. Until that is known it is answered with an error.
- The shape of a patch that changes or deletes a file; only a new file was seen.

## Known problems in version 1

Not to be reproduced.

- **A second process and a bridge** between the tool and its own executor, built on requests the tool marks as experimental, with a list of allowed methods that had to follow every version of the tool.
- **The agent was told otherwise.** The instructions given to the agent said that Arbol's permission setting governed its sandbox.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/executor.py
arbol:drivers/codex/arbol_driver_codex/system_prompt.py#render_codex_system_prompt
arbol:product-spec/06-tools-and-permissions.md#Known problems and lessons
-->

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D22 | How do owner MCP servers reach a resumed run, and how is invalid owner configuration reported? | Read the owner tables once at the start of a tools-enabled run and send the same transient config with either thread/start or thread/resume. Missing setup is empty; invalid setup fails with a fixed nonsecret invalid_input message. Scrub owner table strings from vendor diagnostics without changing tool results | Decided 7 October 2026 during SYL-90, a technical choice. The installed stable ThreadStartParams and ThreadResumeParams schemas both accept config; no experimental protocol or persistent copy is needed. Its diagnostic-only redaction scope is superseded by CDX-D25 below |
| CDX-D25 | How is DRV-0.3 enforced when the vendor repeats a private owner MCP value outside a diagnostic? | Redact the known literal owner-table strings recursively in all emitted event values and keys, and in text output; preserve JSON shapes and use the redacted answer for continuity fingerprints. Credential files remain unread. Transient requests to the vendor retain the original MCP values | Decided 7 October 2026 during SYL-92, a technical correction: diagnostic-only scrubbing allowed a private value to appear in an ordinary event, contrary to DRV-0.3. C7 checks these surfaces |
| CDX-D21 | How are child threads tracked when the tool reports spawning through collabAgentToolCall? | A successfully completed spawnAgent item announces every receiverThreadIds thread, attributed to that item's call identifier. Buffer foreign-thread notifications only while a known spawnAgent call is in progress, replay matching announced receivers, and pass over the rest with the existing single notice. Track these children for waiting and concurrent interruption like subAgentActivity children. Keep the tool name spawnAgent and emit its call completion once | Decided 7 October 2026 during SYL-89, a technical choice after the first live stopping check exposed this second form; `stop.collaboration-spawn`, `live.stopping`; current Python checks: `Mapper.test_collaboration_concurrent_receivers_and_nested_spawn_discovery` and `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`. The earlier live result is historical TypeScript evidence |
| CDX-D8 | Drop version 1's second process per turn, the `codex exec-server` that Arbol started and bridged so that it owned the execution of the agent's commands? | Yes. The app-server runs its tools itself, as it does for anyone who uses `codex`, under the sandbox and approval settings of the request. Given up: Arbol filtering each request between the two | Decided 5 October 2026 by the owner: the proposed default (SYL-10) |
| CDX-D9 | Which level does a caller use for this route by default? | The caller's choice (DRV-D13) | Decided 6 October 2026 by the owner: there are no levels. Every run with tools is unrestricted, as in version 1 (DRV-D12, SYL-44) |
| CDX-D10 | Is the caller's message for a deny delivered to the agent some other way? | No. The tool has no place for it | Withdrawn 6 October 2026: nothing asks, so nothing is denied (SYL-67) |
| CDX-D13 | Which of the tool's other parts are switched on? | None in the first release. MCP servers, plug-ins and applications, memories, image generation, browser and computer use, hooks, skill search, tool suggestions and goals stay off, because each depends on something outside the request | Decided 6 October 2026 by the owner, against the proposed default: nothing of `codex` is switched off but its own memories, as the owner said later that day. Every other part is as the tool ships it (DRV-D26, SYL-71) |
