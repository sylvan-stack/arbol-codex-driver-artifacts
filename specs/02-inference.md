---
role: authored
spec: CDX-2
status: implemented
---
# Codex Driver · 02 Inference

How the Codex Driver meets [DRV-2](../../arbol/driver-contract/02-inference.md) with `codex app-server`. Every run is one app-server process, started in the Subscription's home, given one thread and one turn, and ended when the turn is over. It matters because the installed tool behaves differently from what version 1 assumed in ways that decide the design: interrupting a turn does not stop the command it runs, a missing login is noticed only after fifteen seconds of retries, and neither model nor effort is checked before the vendor rejects them.

Everything stated here about the installed tool was observed on 5 October 2026 with `codex-cli` 0.159.2 and is recorded in the [probe record](../research/tool-probes-2026-10-05.md).

## Scope

Covered: the process of a run and its configuration, the handshake, threads and conversation continuity, what is sent for a turn, the mapping from the tool's notifications to contract events, usage, ending and stopping a run.

Not covered: the contract (DRV-2); sandbox and approval settings, and which parts of the tool are switched off (CDX-3); the mapping of failures to error codes, rate-limit information and time limits (CDX-4).

## Behaviour

### One process per run

A run starts one `codex app-server` process with the Subscription's home as `CODEX_HOME`, the request's working folder as its working directory, the environment of [CDX-1](01-subscriptions.md), and the request's extra search-path folders appended to the search path. The process is in a process group of its own. It speaks one JSON object per line on standard input and output; its log goes to standard error, of which the Driver keeps the last 64 KiB for error reports.

When the turn is over, the Driver closes the process's standard input. The process then exits within a fraction of a second and takes every command it started with it. This is how every run ends, whatever its outcome, because it is the one way of ending that was seen to leave nothing running.

Observed with the installed tool: the process exits with code 0 about 20 ms after its input closes or after a termination signal, also in the middle of a turn, and writes nothing more. Two processes on one home ran turns at the same time without errors.

Observed in version 1: two processes per turn, the app-server and a separate executor behind a bridge, each started through a launch job. The app-server was stopped by signal; commands the executor had started were left running.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#control_argv`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/tool_process.py#ToolProcess._cleanup`

### Configuration of the home

Before the first start in a home the Driver writes the tool's configuration file there, and rewrites it whenever its own version of that file changes. The file holds housekeeping and one switch: it switches off the check for updates and analytics, sets web search to `live`, and switches off the tool's own memories. It switches no other part of the tool off (CDX-3). After the handshake the Driver reads the effective configuration back and compares the settings it relies on. A run does not start when the tool reports the file as invalid, ignores a setting in it, or shows another value than the one written.

Observed with the installed tool: a fresh home without such a file clones a plug-in catalogue of 88 MB at start; with plug-in features switched off in the file, it does not. A file the tool cannot read does not stop it: it warns and continues with its defaults. Unknown keys are ignored with a warning.

Observed in version 1: the configuration belonged to the Leather Bag. Arbol passed overrides on the command line, checked what took effect, and refused the turn when the file held anything it could not represent.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#validate_config`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#control_argv`

### Handshake and checks before the turn

| Step | Request | What the Driver does with the answer |
|---|---|---|
| 1 | `initialize` with the Driver's name and version | Compares `codexHome` with the Subscription's home (CDX-1.3). Notes the tool's version |
| 2 | `initialized` (notification) | |
| 3 | `config/read` | The comparison described above |
| 4 | `account/read` | No ChatGPT account: the run is refused with `not_signed_in` and the Subscription moves to `needs_attention` |
| 5 | `model/list` | The request's model must be in the list and its effort among that model's efforts; otherwise the run is refused with `invalid_input` |

Every request of the handshake has 30 seconds to be answered. A request the tool sends that the Driver does not know is answered with an error, never left open.

Observed with the installed tool: without a login a turn is accepted and fails only after about 15 seconds of reconnecting. An unknown model is accepted at `thread/start` and fails in the turn; an effort the model does not list is either rejected by the vendor or silently accepted. `account/read` and `model/list` are answered locally and at once.

Observed in version 1: no account check and no model check. The request timeout was 30 seconds, and unknown requests from the tool were answered with an error.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`

### Threads and continuity

| Continuity | What the Driver sends |
|---|---|
| `fresh` | `thread/start` for a saved thread |
| `resumed` | `thread/resume` with the thread the Driver's map names, in the new process |
| `rebuilt` | `thread/start` for a new saved thread, then `thread/inject_items` with the earlier messages, then the turn |

The Driver's map (DRV-2) names, for a chat session and a Subscription, the tool's thread and what it covers. An entry is written only after a completed run on a saved thread, and removed when a run on that thread ends any other way. The Driver resumes when every check of DRV-6 holds and `thread/resume` succeeds. A thread that is gone leads to a rebuild with the reason `conversation_gone`, any other refusal of the resume with `resume_refused`.

For a rebuild the Driver inserts the earlier messages into the new thread with `thread/inject_items`, as messages of the user and of the assistant in their order, before it starts the turn. A tool call of the history is inserted as a `function_call` item followed by a `function_call_output` item with its result, under the name it was reported with, also when the other Driver reported it. A command in a terminal is therefore inserted under the name `shell`. That is not a name of the installed tool's own, which calls its command tools `exec_command` and `exec`; the model was seen to use calls inserted this way. A picture of an earlier message is inserted with that message, as `input_image` content. The thread then holds them as if the tool had saved that conversation itself. Where a tool version refuses the request, the fallback is version 1's way: the first input is one text with a heading and the earlier messages, each labelled with its role, then a heading and the new message.

A run with all tools off and no working folder uses a thread the tool does not save.

Observed with the installed tool: a saved thread is a file under the home's `sessions` folder. In a new process it must be resumed before a turn can be started on it. After a resume the model knew a word given in the first turn and the command it had run then. The tool restores the thread's effort but not its service tier. A thread that is not saved cannot be resumed, read or forked. `thread/delete` removes a saved thread completely. Items inserted with `thread/inject_items` were used by the model in three real turns on 6 October 2026: plain messages; a tool call with its result; and a picture together with a tool call under a name the tool has none for (`Bash`, the `claude` tool's own name for a command).

Historical TypeScript live observation on 7 October 2026, SYL-88 on `test-chatgpt`, `gpt-5.6-luna` at low effort: a second run resumed and recalled the first word and actual terminal output; editing the first message rebuilt with `history_differs` and retained the earlier tool result; changing the system prompt rebuilt with `system_prompt_changed` and followed the new prompt. The rebuilt raw history stores its terminal `function_call` with name `shell`, as `probe.continuity` confirms. Asked for the historical tool name, the model answered `exec_command`: its visible description can use its own terminal name although the stored inserted name is `shell`. `thread/read` shows no inserted turns. Evidence: `research/continuity-2026-10-07.json` and `research/continuity-protocol-2026-10-07.json`.

Observed in version 1: a new unsaved thread for every attempt; the earlier conversation written into the prompt under the headings "Earlier conversation in this Chat Session" and "Current request", after the system prompt; all earlier images attached again on every turn.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#render_prompt`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/images.py#prepare_images`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`

### Building a thread from a history

A rebuilt thread is a new saved thread into which the Driver inserts the history, with one request `thread/inject_items { threadId, items }` sent after `thread/start` and before the turn. The items have the form of the vendor's Responses interface and are in the order of the history:

| History item | Items |
|---|---|
| A message of the user | `{ "type": "message", "role": "user", "content": [ … ] }`: an `input_text` part with the text, then one `input_image` part per picture, whose `image_url` is a `data:` address with the picture's media type and base64 data |
| A message of the assistant | `{ "type": "message", "role": "assistant", "content": [ { "type": "output_text", "text": … }, … ] }`: any pictures supplied with that message follow as `input_image` parts, by the same rule as a user message. If the tool refuses these parts, the text fallback carries the pictures |
| A tool call | `{ "type": "function_call", "name", "arguments", "call_id" }`, then `{ "type": "function_call_output", "call_id", "output" }` |

For a tool call:

- The Driver makes the `call_id` up: `call_` followed by 24 random letters and digits, the same in both items.
- `arguments` is the call's input as JSON text. A `shell` call keeps the name `shell`, and its arguments are its `command` and, where it named one, its `cwd`.
- Every other call keeps the name it was reported with, also one the other Driver reported.
- `output` is the result as text, by the rule of DRV-2.

The tool answers `{}`. Inserted items are history for the model and not turns: `thread/read` shows none of them. Where the tool refuses the request, the Driver sends the text form of DRV-2 as the turn's input.

### The turn

`turn/start` carries the thread, the input, and on every turn, resumed or not: model, effort, service tier, and the approval and sandbox settings of CDX-3. The system prompt of the request is sent as `developerInstructions` when the thread is started, so the tool's own base prompt, which describes its tools, stays in place. The Driver asks for reasoning summaries. The owner's own MCP servers go into the transient `config` of `thread/start` or `thread/resume` for a run with tools (CDX-3).

Images of the message are written to a temporary folder as files and passed as local images; the folder is removed when the run has ended.

Observed with the installed tool: `baseInstructions` replaces the tool's built-in prompt and `developerInstructions` adds to it; both took effect. `turn/start` accepts model, effort, service tier, approval and sandbox overrides.

Observed in version 1: the system prompt was the first part of the user's input, and the tool's instruction fields carried one fixed sentence.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#render_prompt`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`

### The requests in full

What the Driver sends, by name. A request that takes parameters needs `params`, even an empty one.

| Request | Parameters |
|---|---|
| `initialize` | `clientInfo: { name: "arbol-codex-driver", version }`, the version being the Driver's package version |
| `initialized` | None. A notification |
| `config/read` | `{}` |
| `account/read` | `{}` |
| `model/list` | `{}`, and again with the cursor of the answer for as long as there is one |
| `thread/start` | `cwd`, `model`, `approvalPolicy`, `sandbox`; `serviceTier` where the request names one; `developerInstructions` where the request has a system prompt; `config` with the owner's MCP servers under `mcp_servers` (CDX-3); `ephemeral: true` only for a run without tools and without a working folder |
| `thread/resume` | `threadId`, `model` with the validated model selected for this run, so the thread response reports the current model instead of its previous one; transient `config` with the owner's MCP servers under `mcp_servers` for a run with tools |
| `thread/inject_items` | `threadId`, `items` |
| `turn/start` | `threadId`, `input`, `model`, `effort`, `summary: "detailed"`, `approvalPolicy`, `sandboxPolicy`; `serviceTier` where the request names one |
| `turn/interrupt` | `threadId`, `turnId` |

`approvalPolicy` is always `never`. On `thread/start` the sandbox is the word `danger-full-access`, or `read-only` for a run without tools. On `turn/start` it is `sandboxPolicy: { "type": "dangerFullAccess" }`, or `{ "type": "readOnly", "networkAccess": false }` for a run without tools. `input` is a list: `{ "type": "text", "text": … }` for the message, then one item per picture that names the picture's file.

Observed with the installed tool: `thread/start {}` is accepted and takes the process's folder, the configured model, the approval policy `on-request` and a read-only sandbox, which is why the Driver names all four. `turn/start` needs `threadId` and `input`. `turn/start` with `summary: "detailed"` produced a reasoning summary. An unknown value for the sandbox is refused with a message that lists the four that exist.

Observed on 6 October 2026, real runs on one thread: `thread/resume` accepts `developerInstructions` among other fields, but the continued thread answered by the instructions of its first run, both when the resume named other instructions and when it named none. A changed system prompt is therefore a reason to build a new thread (DRV-6).

### From notifications to events

| The tool sends | The Driver emits |
|---|---|
| Result of `turn/start` | `started`, with the continuity, the model the thread reports and the tool's version |
| `item/agentMessage/delta` | `text_delta` |
| `item/completed`, item `agentMessage` | `text` with the whole text |
| `item/reasoning/summaryTextDelta` | `thinking_delta` |
| `item/completed`, item `reasoning` | `thinking` with the summary parts joined by blank lines; nothing when the summary is empty |
| `item/started`, item `commandExecution` | `tool_started`, name `shell`, input: the plain command, without the launcher the tool wraps around it, and the working directory (DRV-3.19) |
| `item/commandExecution/outputDelta` | `tool_output_delta` |
| `item/completed`, item `commandExecution` | `tool_finished`: success when the status is `completed` and the exit code is 0; the result is the collected output and the exit code. Status `declined`: failure with the error "declined" |
| `item/started`, item `fileChange` | `tool_started`, name `apply_patch`, input: the list of changes with path, kind and content |
| `item/completed`, item `fileChange` | `tool_finished`: success when the status is `completed`; `declined` and `failed` as failures |
| `item/started` and `item/completed` of another tool-like item type | `tool_started` and `tool_finished` with the item type as the name |
| A request for approval or for an answer from the person | Not expected, since nothing asks. Answered at once as CDX-3 says, with a `notice` |
| `serverRequest/resolved` | Nothing |
| `thread/tokenUsage/updated` | `usage` |
| `error` with `willRetry` true | `notice` with the tool's message |
| `model/rerouted`, `warning`, `deprecationNotice` | `notice`; a reroute also changes the model reported in `usage` |
| `error` with `willRetry` false, then `turn/completed` with status `failed` | `finished`, outcome `failed`, with the error mapped by CDX-4 |
| `turn/completed` with status `completed` | `finished`, outcome `completed` |
| `turn/completed` with status `interrupted` | `finished`, outcome `cancelled` when the caller asked for the stop; otherwise `failed` |
| The process ends, or its output ends, before `turn/completed` | `finished`, outcome `failed`, with the end of the tool's log |
| Items of the user's own message, `thread/started`, `turn/started`, `thread/status/changed`, `turn/diff/updated`, `account/updated`, `remoteControl/status/changed` | Nothing |

A notification that names the run's thread and another turn fails the run. A notification that names another thread belongs to a sub-agent when a `subAgentActivity` item or a successfully completed `collabAgentToolCall` of tool `spawnAgent` announced that thread, and is then reported as CDX-3 says. Notifications that precede the completion of a known spawn call are buffered and replayed as CDX-3 says. A notification of any other thread is passed over, with one `notice` for the run.

`item/completed` can arrive after `turn/completed`, and a command the agent left running goes on after it. After `turn/completed` the Driver therefore waits for every command that is still running until the tool reports it complete, and for every sub-agent whose turn is still active until that turn has completed (DRV-3.32). For any other call that is still open it waits up to 2 seconds and then closes it itself as interrupted. Only then does it emit `finished`.

Observed with the installed tool: text arrives in deltas and whole in the completed item; an interrupted turn delivers no completed item for the unfinished message. Reasoning arrived as summary deltas only, and not at all for trivial turns at low effort. A slow command delivered its output line by line; an instant one only in the completed item. Every turn ended with exactly one `turn/completed`; a failed one was preceded by an `error` with the same content.

Observed on 6 October 2026, one real run: the agent left a command of 40 seconds running and ended its turn. `turn/completed` arrived with the command's item still in progress, the command ran on as a child of the app-server, and its `item/completed`, with the output and exit code 0, arrived 36 seconds after the turn had completed. No further turn started: the agent was not told.

Observed in version 1: each notification was first rewritten into the record shape of the tool's retired non-interactive mode and then mapped. Text and reasoning were emitted only when an item was complete, and command output only when the command had finished.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#exec_events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#map_exec_event`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.events`

### Usage

The tool reports usage once per request to the model, with the counts of that request and the running total of the whole thread. The run's totals are the sum of the per-request counts since the run started. Input counts include cached input, and output counts include reasoning output, as the tool reports them; cached and reasoning counts are also given on their own. There is no cost: a ChatGPT Subscription has none per run.

Observed with the installed tool: one report in a text turn and three in a turn with two tool calls. The thread total continues across turns and across a resume in a new process. An interrupted turn produced no report.

Observed in version 1: only the per-request input and output counts were used, each emitted as an increment for Root to add up.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#usage_from`

### Stopping a run

| Step | Action | Limit |
|---|---|---|
| 1 | Concurrent `turn/interrupt` requests for the active main turn and every active sub-agent turn | One deadline, 2 seconds after the stop was asked for |
| 2 | Wait for the `turn/completed` of each of them | Until 2 seconds after the stop was asked for |
| 3 | Close the process's input and wait for it to exit | Only until the same deadline 2 seconds after the stop was asked for; no new grace period |
| 4 | End the verified remaining process groups by signal, escalating without a new grace period | Whatever remains of the 15 seconds of DRV-2.16 |

Running tool calls are then closed as interrupted, and `finished` is emitted with outcome `cancelled`. A run that is cancelled or fails leaves no entry in the map and removes the one it was continuing.

Observed with the installed tool: `turn/interrupt` answers at once and the turn completes as `interrupted`, but a command the turn was running keeps running as a child of the app-server and keeps sending output. A `turn/interrupt` for a turn that has already ended was not answered at all. Ending the process ended the command.

Observed on 6 October 2026, real runs with a sub-agent in the middle of a command of 45 seconds. After a `turn/interrupt` for the run's turn alone, that turn completed as `interrupted` and the sub-agent worked on: its command ran to its end, its turn completed 47 seconds later, and an item `subAgentActivity` of kind `completed` then arrived on the run's thread. With a second `turn/interrupt`, for the sub-agent's thread and turn, both turns completed as `interrupted` at once, and the command ran on until the process ended. Closing the process's input in the middle of the sub-agent's command ended the process with status 0 and the command with it. A process that a command had left behind with `nohup … &` was gone when the call was reported complete. A process that had moved into a session of its own was still running after the app-server had exited, with the system's first process as its parent (DRV-D33).

Historical TypeScript live observation on 7 October 2026 during SYL-89, `codex-cli` 0.159.2 on `test-chatgpt`, `gpt-5.6-luna` at low effort: a streamed-answer stop ended as `cancelled` in 52 ms; after the Driver was killed outright during a command, `runs list` recovered its app-server and command groups in 80 ms and removed its record and scratch folder. The first sub-agent check exposed the second announcement form of CDX-D21 and failed. After that form was supported, one focused sub-agent check stopped both turns and the child command in 55 ms, with no verified process group left alive. Evidence: `research/stopping-2026-10-07.json` (the first two checks passed and the initial child check failed), `research/stopping-initial-2026-10-07.json` (retained copy), and `research/stopping-subagent-2026-10-07.json` (focused child check passed). The no-prompt `probe.stopping` also confirmed the stable interrupt and child notification schemas and EOF cleanup, in `research/stopping-protocol-2026-10-07.json`.

Observed in version 1: stop never asked the tool; it ended the app-server by signal.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner.cancel`

## SYL-92 verification, 7 October 2026

SYL-92 passed the complete 38-scenario shared registry for both Python Drivers. Codex also passed 128 unit methods, Ruff and strict mypy from source; its standalone CPython 3.14.8 development candidate passed the same units and all 38 scenarios, and its relocated copy passed metadata and unit checks under a minimal environment. A fresh packaged `dev probe` passed against codex-cli 0.159.2 with zero inference requests. The packaged build gate sent exactly one no-tools ready message through `test-chatgpt`; it completed and reported tokens and usage before/after. The extended five-turn `dev live-check` orchestration and refusal gates passed offline, but the extended vendor run was not requested. Contract and state format remain 1. The first numbered Codex Build is the separate SYL-94 task.

Current records and source/package provenance: `~/Artifacts/arbol-codex-driver/research/conformance-2026-10-07/verification.json`, `coverage-audit.json`, `packaged-probe.json` and `packaged-build-check.txt` in that folder. Dated migration and TypeScript evidence below remains historical; unobserved real vendor failures remain unobserved. The coverage audit retains every former Verified by cell before this update.

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-2.1 | start one app-server process per run, in a process group of its own, with the Subscription's home, the request's working folder and the environment of CDX-1 | DRV-2.21 | Changed | Codex Python: `C18`, `AppServerTests.test_private_home_configuration_clean_environment_and_owner_cleanup`, `Lifecycle.test_control_signals_eof_and_peer_stop_interrupt_once_then_cleanup` |
| CDX-2.2 | write the configuration of a home itself, read the effective configuration back after the handshake, and refuse the run when the tool reports the file invalid, ignores a setting or shows another value | DRV-3.25 | Changed | Codex Python: `AppServerTests.test_private_home_configuration_clean_environment_and_owner_cleanup`, `AppServerTests.test_startup_wrong_home_config_and_cancellation_gives_eof_before_force` |
| CDX-2.3 | check the account with `account/read` before starting a turn, and refuse the run with `not_signed_in` when the home holds no ChatGPT account | DRV-2.2 | New | Codex Python: `C40`, `Accounts.test_unsigned_refusals_and_malformed_state_do_not_start_vendor_or_disclose_contents`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` |
| CDX-2.4 | check the request's model and effort against `model/list` before starting a turn | DRV-2.2 | New | Codex Python: `C40`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers`, `Requests.test_request_defaults_and_ignored_settings_effort_provenance` |
| CDX-2.5 | answer every request of the tool it does not know with an error | DRV-2.3 | Kept | Codex Python: `C25`, `C35`, `AppServerTests.test_fragmented_utf8_early_notifications_burst_and_unknown_request`, `AppServerTests.test_predicate_errors_settle_only_affected_waiter` |
| CDX-2.6 | abandon a handshake request that is not answered within 30 seconds and fail the run | DRV-2.3 | Kept | Codex Python: `AppServerTests.test_malformed_oversized_boolean_id_exit_and_internal_request_timeout`, `AppServerTests.test_startup_wrong_home_config_and_cancellation_gives_eof_before_force`, `AppServerTests.test_timeout_and_cancellation_include_blocked_stdin_drain` |
| CDX-2.7 | use a saved thread for every run that has tools or a working folder, and a thread the tool does not save otherwise | DRV-2.12 | Changed | Codex Python: `C14`, `C19`, `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt`, `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread` |
| CDX-2.8 | resume a thread only through `thread/resume` in the run's own process, and rebuild when the resume is refused | DRV-2.12 | Changed | Codex Python: `C14`, `Continuity.test_resume_vendor_refusal_and_missing_rollout_rebuild_then_failed_resume_invalidates_map` |
| CDX-2.9 | for a rebuild, insert the earlier messages with their images and the tool calls into the new thread with `thread/inject_items` before the turn, and fall back to one labelled text before the new message when the tool refuses the request | DRV-2.11 | Changed | Codex Python: `C14`, `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt`, `Foundation.test_history_native_pairing_shell_fields_and_private_ordered_images` |
| CDX-2.10 | send the system prompt as `developerInstructions` and nothing of its own in the instruction fields | DRV-2.1 | Changed | Codex Python: `C10`, `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt` |
| CDX-2.11 | send model, effort, service tier, approval and sandbox settings with every `turn/start`, also on a resumed thread | DRV-2.1 | New | Codex Python: `C10`, `C19`, `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread` |
| CDX-2.12 | map the tool's notifications to events by the table above, fail the run on a notification that names its thread and another turn, report one that names the thread of a sub-agent of the run as CDX-3 says, and pass over one that names any other thread, with one `notice` | DRV-2.3 | Changed | Codex Python: `C10`, `C11`, `C12`, `C13`, `C35`, `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`, `Mapper.test_collaboration_concurrent_receivers_and_nested_spawn_discovery`, `Mapper.test_protocol_malformed_foreign_notices_outcome_and_utf8_truncation`, `Mapper.test_text_authoritative_blocks_reasoning_usage_dedup_and_reroute` |
| CDX-2.13 | emit `text` from the completed message item, so that a caller that missed deltas still receives the whole text | DRV-2.4 | New | Codex Python: `C10`, `Mapper.test_text_authoritative_blocks_reasoning_usage_dedup_and_reroute`, `OutputTests.test_serialized_output_gapless_events_lone_surrogates_and_cancelled_blocked_flush` |
| CDX-2.14 | after `turn/completed`, wait for commands still running and for sub-agents still at work until the tool reports them ended, and up to 2 seconds for any other open call, then close the rest itself, before emitting `finished` | DRV-2.6 | New | Codex Python: `C11`, `C35`, `C42`, `Lifecycle.test_main_completion_waits_for_late_child_and_closes_spawn_once`, `Mapper.test_shell_mapping_late_results_failures_and_interrupted_calls_once`, `ToolRuns.test_late_noncommand_child_tool_closes_after_completed_turns_and_background_work` |
| CDX-2.15 | report as usage the sum of the per-request counts since the run started, with cached and reasoning counts, and the model the tool reports | DRV-2.15 | Changed | Codex Python: `C13`, `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread`, `Mapper.test_text_authoritative_blocks_reasoning_usage_dedup_and_reroute` |
| CDX-2.16 | end every run by closing the process's input, and end the process group by signal when the process has not exited after 2 seconds; for a stop, anchor this escalation to the original stop time without a new EOF or signal grace period | DRV-2.19 | Changed | Codex Python: `C15`, `C17`, `C38`, `AppServerTests.test_cleanup_survives_capture_failure_and_ends_ignoring_descendant`, `AppServerTests.test_startup_wrong_home_config_and_cancellation_gives_eof_before_force`, `ForcedProcessGroupTests.test_immediate_kill_refuses_reused_or_wrong_group_leaders`, `Lifecycle.test_blocked_output_cleanup_and_final_deadline_for_signal_and_control`, `Lifecycle.test_broken_output_cancels_native_turn_and_cleans_workers`, `Lifecycle.test_ignored_interrupt_and_stop_during_normal_eof_use_same_force_anchor` |
| CDX-2.17 | on stop send `turn/interrupt` for the run's turn and for the active turn of every sub-agent, give those requests and the wait for the turns' end 2 seconds, then end the process as in CDX-2.16 | DRV-2.16 | Changed | Codex Python: `C15`, `Lifecycle.test_accepted_turn_before_rpc_reply_is_interrupted`, `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`, `Lifecycle.test_control_signals_eof_and_peer_stop_interrupt_once_then_cleanup`, `Lifecycle.test_ignored_interrupt_and_stop_during_normal_eof_use_same_force_anchor` |
| CDX-2.18 | write an entry to the map only for a completed run on a saved thread | DRV-2.12 | New | Codex Python: `C14`, `Continuity.test_resume_vendor_refusal_and_missing_rollout_rebuild_then_failed_resume_invalidates_map`, `Foundation.test_continuity_selection_order_conditional_settlement_and_killed_owner` |
| CDX-2.19 | write message images to a temporary folder for the run and remove it when the run has ended | DRV-2.23 | Kept | Codex Python: `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt`, `Foundation.test_history_native_pairing_shell_fields_and_private_ordered_images` |
| CDX-2.20 | use no request the tool marks as experimental in a run | CDX-0.5 | New | Codex Python: `C10`, `C14`, `C19`, `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt` |
| CDX-2.21 | insert a history with one `thread/inject_items` request, in the item forms, with the made-up call identifiers and the result texts stated above, and send the text form of DRV-2 where the tool refuses the request | DRV-2.36 | New | Codex Python: `C14`, `Continuity.test_native_history_and_visible_text_fallback_preserve_tools_images_and_system_prompt`, `Foundation.test_history_native_pairing_shell_fields_and_private_ordered_images`, `Foundation.test_migration_golden_vectors_and_nonmutating_stream_snapshots` |

## Python migration verification on 7 October 2026

SYL-95 ports the implemented run, continuity and stopping paths to pinned CPython 3.14.8. The `Class.method` references above name current unittest methods in `tests/`, run from source and the embedded interpreter of the standalone development candidate, including relocation to a path containing spaces. The independent Node baseline supplies 14 history/fingerprint vectors and 13 JSON serialization vectors; the mixed-language harness also exercises native Unicode/image continuity, duplicate run identifiers, peer stop in both directions and killed-owner recovery. This is a development candidate; SYL-90 tools are now verified separately in CDX-3; SYL-91 errors, retry stopping, run usage and clocks are now verified in CDX-4; SYL-92 and SYL-94 remain pending. No Python live inference turn was sent for the migration.

The retained run wrapper invokes `C10` “Fresh run and request defaults”, `C11` “Text before and after a shell call”, `C12` “Error flag under a success subtype”, `C13` “Usage totals and absent values”, `C18` “Concurrent runs stay independent”, `C19` “No tools and no leftover work folder”, `C20` “Large tool results are cut”, `C42` “Failure preserves output and unfinished calls” and `C43` “State failure has one final event”. Its `C33` scope remains no control input and a JSON request from stdin only; its `C40` scope remains unsigned runs and fresh-run directory, duplicate ID, model, effort and tier refusals. Continuity invokes `C14` “Resume or rebuild the caller conversation”. Stopping invokes `C15` “Stop closes partial output, calls, questions and sub-agents”, `C16` “Stopping ended or unknown runs succeeds”, `C17` “Every end path clears shell process groups” and `C38` “Recover a killed Driver and protect durable state”; its separate `C33` scope remains no control, stdin request, malformed control, active records and runs stop, with caller questions excluded by CDX-3.13. These are the original scenarios and explicit scopes; only executable selection changed in the wrappers.

Evidence: `research/python-migration-2026-10-07/verification.json`, `research/python-migration-2026-10-07/packaged-unit.txt`, `research/python-migration-2026-10-07/scoped-conformance-runs.txt`, `research/python-migration-2026-10-07/scoped-conformance-continuity.txt`, `research/python-migration-2026-10-07/scoped-conformance-stops.txt`, `research/python-migration-2026-10-07/compatibility.json`, `research/python-migration-2026-10-07/no-prompt-probes.json` and `research/python-migration-2026-10-07/standalone-rehearsal.json`. Prior `probe.run-protocol`, `probe.continuity`, `probe.stopping`, `live.run`, `live.no-tools`, `live.continuity` and `live.stopping` names refer to historical TypeScript evidence. Their observations and unsuccessful attempts remain retained, and their live results are not reported as fresh Python live coverage.

## Not established

- Which of a catalog entry's `id` and `model` a request must name when they differ; they were equal for every model.
- What the tool does with an effort the model does not list; one such turn completed without any notice.
- Whether two processes can resume the same thread at once. A lock file per loaded thread exists.
- How image inputs behave in a real vendor turn. On 7 October 2026, SYL-86 confirmed the current-message form `localImage { path }` with `probe.run-protocol` against the installed tool's generated stable `UserInput` schema and exercised private files with `run.images`; no live image turn has yet been sent.
- How large a history one `thread/inject_items` request accepts. SYL-88 inserted nine items in its no-prompt check, including a failed shell call with output, nonzero exit and error text, and pictures on user and assistant messages. `probe.continuity` confirms the stored native forms; no live failed-call or history-image turn has been sent.

## Known problems in version 1

Not to be reproduced. The legacy map in [CDX-0](00-overview-and-legacy-map.md) lists them by part; those that concern a run:

- **No streaming.** The Leather Bag saw nothing of an answer until an item was complete, and nothing of a command's output until it had finished.
- **The agent started every message from a transcript.** Tool calls and their results from earlier messages were not in it.
- **A stop left commands running**, and nothing told the tool that the turn was over.
- **A wrong model, a wrong effort or a missing login surfaced late**, as a vendor error in the middle of a turn.
- **Usage dropped what the tool reported**: cached input, reasoning output, and the model that actually ran.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:product-spec/03-turn-execution.md#Known problems and lessons`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D20 | How does stop stay bounded and clean up a run after its caller or Driver disappears? | Use one deadline 2 seconds after the first stop for all interrupt requests and turn completions. Send interrupts concurrently for the main turn and every announced active sub-agent turn, including one first reported before that deadline; never interrupt a turn already reported complete. Keep draining vendor notifications during stop even when event output has failed. Event backpressure is interruptible so it cannot delay process cleanup. Give final event writes only the remaining stop budget; if the caller still accepts no output at that deadline, close event output and end cancelled after cleanup. Before closing app-server input, collect verified process and process-group owners for its commands and descendants in the run's scratch folder; a vendor command identifier is not an operating-system process identity. Close input and give it only what remains until the original stop time plus 2 seconds; ordinary completion allows 2 seconds after input closes. On stop, end verified remaining groups at the original 2-second deadline without a fresh EOF or signal grace period, within the 15-second total bound. Publish the launcher's process identifier and start time in scratch before exec, and record the app-server owner as soon as it starts, so killed-run cleanup can use the recovery election and conditional map removal of DRV-D40. Cleanup runs outside the Subscription lock | Decided 7 October 2026 during SYL-89, a technical choice; `C15`, `C16`, `C17`, `C33` (Codex scope), `C38`, `stop.paths`, `stop.recovery`, `stop.backpressure`, `probe.stopping`, `live.stopping`; current Python migration checks: `Lifecycle.test_control_signals_eof_and_peer_stop_interrupt_once_then_cleanup`, `Lifecycle.test_active_nested_and_late_discovered_children_are_interrupted_and_attributed`, `Lifecycle.test_accepted_turn_before_rpc_reply_is_interrupted`, `Lifecycle.test_ignored_interrupt_and_stop_during_normal_eof_use_same_force_anchor`, `Lifecycle.test_blocked_output_cleanup_and_final_deadline_for_signal_and_control` and guarded process-group tests. Earlier probe/live names are historical TypeScript evidence |
| CDX-D19 | Which model is reported when a resumed turn selects a different model? | Send the validated model with thread/resume as well as turn/start. The resume response then supplies the current model for started and the initial usage state; later model/rerouted notifications still replace it | Decided 7 October 2026 during SYL-88, a technical choice; continuity.run and probe.continuity; current Python migration checks: `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread`. Earlier probe/live names are historical TypeScript evidence |
| CDX-D18 | How are notifications replayed during a resume kept out of the new run? | Drain notifications already queued before sending turn/start. Keep startup warnings and deprecation notices for the event stream; discard restored turn status and prior token usage. Notifications received from turn/start onward stay in their ordered queue, including those before its response. On a resumed thread, a delayed usage replay that has no turn identifier or names a known earlier turn is also passed over; other notifications for a different turn still fail the run | Decided 7 October 2026 during SYL-88, a technical choice; continuity.run and probe.continuity; current Python migration checks: `Continuity.test_resume_overrides_and_delayed_restored_usage_do_not_count_previous_thread` and `AppServerTests.test_fragmented_utf8_early_notifications_burst_and_unknown_request`. Earlier probe/live names are historical TypeScript evidence |
| CDX-D15 | How are inference notifications kept in order across startup and a slow event consumer? | Keep one ordered notification queue in the JSONL transport, including notifications received before turn/start answers. Map notifications directly after the accepted turn identifies its thread and turn. Assign gapless sequence numbers synchronously and serialize stdout writes through one asynchronous chain (Python tasks from SYL-95); a failed write is observed by the runner. Never emit finished from the mapper: cleanup and closing unfinished calls precede that event | Decided 7 October 2026 during SYL-86, a technical choice; C10, C42, run.protocol and run.lifecycle; current Python migration checks: `AppServerTests.test_notification_backpressure_preserves_long_stream_and_wakes_for_rpc`, `OutputTests.test_serialized_output_gapless_events_lone_surrogates_and_cancelled_blocked_flush` and `C10`/`C42`. Earlier probe/live names are historical TypeScript evidence |
| CDX-D16 | May inference use the model catalog's built-in fallback? | No. Read model/list without its subscription-command fallback and validate the chosen model, effort and service tier before thread/start. An unavailable named model or unsupported explicit effort is refused; no other model is put in its place. A failed turn is not started again by the Driver | Decided 7 October 2026 during SYL-86, a technical choice; C40, run.validation and run.failures; current Python migration checks: `C40` (fresh-run refusal scope), `C12` and `C42` (one run; no Driver retry). Earlier probe/live names are historical TypeScript evidence |
| CDX-D17 | How are tool diagnostics retained without forwarding raw stderr? | Drain stderr into an in-memory UTF-8 tail bounded to 64 KiB. On a failed transport, use the common error helper to retain at most the final 1 KiB as the diagnostic excerpt; never persist the tail or write raw tool stderr to the command's stderr. The event writer owns stdout and serializes its writes | Decided 7 October 2026 during SYL-86, a technical choice; app-server.run-stream, run.failures and errors; current Python migration checks: `AppServerTests.test_authentication_rejection_is_specific_and_diagnostics_are_bounded` and `C42`. Earlier probe/live names are historical TypeScript evidence |
| CDX-D4 | One app-server per run, or one per Subscription shared by its runs? | One per run. Ending the process is the only stop seen to end the commands of a turn, and a failure stays within its run. The cost is a start of the tool per message | Decided 6 October 2026 by the owner: one per run (SYL-65) |
| CDX-D5 | System prompt as `developerInstructions` or as `baseInstructions`? | `developerInstructions`. The other replaces the tool's own prompt, which describes its tools, and saves about 4,000 input tokens per request | Decided 6 October 2026 by the owner: `developerInstructions`. The agent gets the tool's own instructions and Arbol's (SYL-56) |
| CDX-D6 | How long are saved threads kept in a Subscription's home? | 30 days after their last run, removed with `thread/delete` at the start of a later run. A removed thread only costs a rebuild | Decided 6 October 2026 by the owner, against the proposed default: a Driver never removes a saved thread. Cleaning up is a feature of Arbol, and how Arbol reaches these files is settled with that feature (SYL-58). The one-off run of DRV-D11 saves no thread in the first place |
| CDX-D7 | Are reasoning summaries requested? | Yes. They are the only reasoning text the tool releases | Decided 6 October 2026 by the owner: yes (SYL-66) |
