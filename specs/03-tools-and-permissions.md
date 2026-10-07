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
| MCP servers | The tables `[mcp_servers]` in the file `~/.codex/config.toml` | The Driver reads those tables when a run starts and hands them to the tool in the `config` of `thread/start`. They are written nowhere |

The tables can hold secrets of the owner's, such as a key in a server's environment. The Driver passes the tables on as they are and never writes, logs or reports them (DRV-0.3). Nothing else of the owner's own `~/.codex` reaches a run: no other setting of that file, and not the login.

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
| CDX-3.1 | run commands and patches through the app-server itself, without a separate executor process | DRV-3.20 | Changed | `C11`, `run.tools`, `run.lifecycle` (commands and baseline patches through the single app-server) |
| CDX-3.2 | write `memories = false` and no other feature switch into the configuration of a home, so that every other part of the tool is as the tool ships it, and set `web_search` to `live` | DRV-3.25 | Changed | `app-server.home`, `app-server.validation`, `run.lifecycle` (memories only, live web search and configuration readback) |
| CDX-3.3 | send the sandbox `danger-full-access` and the approval policy `never` when the thread of a run with tools is started and with every turn | DRV-3.21 | Changed | `run.lifecycle`, `live.run` (fresh thread and turn; resumed turns pending SYL-88) |
| CDX-3.9 | answer a command approval or a file-change approval that arrives nonetheless with `accept` and every other request of the tool with an error, and emit a `notice` | DRV-3.22 | Changed | unit |
| CDX-3.11 | for a run without tools, send the sandbox `read-only` and the approval policy `never`, use an empty folder of its own when the request names no working folder, and report a tool call that occurs nonetheless without failing the run | DRV-2.20 | Changed | `C19`, `run.images`, `live.no-tools` |
| CDX-3.12 | set `parentCallId` on every event that reports what a sub-agent did, and keep a sub-agent's text out of the answer: a sub-agent's work is every notification that names the thread a `subAgentActivity` item of the run announced | DRV-3.24 | New | contract, live |
| CDX-3.13 | emit no question from the agent, for as long as the tool offers such questions only in its experimental mode | DRV-3.26 | Kept | unit |
| CDX-3.14 | hand the `[mcp_servers]` tables of the owner's `~/.codex/config.toml` to the tool in the `config` of `thread/start` for a run with tools, and write, log and report them nowhere; read nothing else of the owner's `~/.codex` and write nothing there | DRV-3.31 | New | contract, probe |
| CDX-3.15 | keep a run going after its turn has completed while a sub-agent's turn is still active, and stop a sub-agent with a `turn/interrupt` for its own thread and turn | DRV-3.32 | New | contract, live |

CDX-3.4 to CDX-3.8 and CDX-3.10 described levels of asking and approval questions. They were withdrawn on 6 October 2026 with DRV-D12, and their numbers are not used again.

## Not established

- A sub-agent the agent does not wait for, a stop while a sub-agent works, and what `collabAgentToolCall` items other than `wait` carry.
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
| CDX-D8 | Drop version 1's second process per turn, the `codex exec-server` that Arbol started and bridged so that it owned the execution of the agent's commands? | Yes. The app-server runs its tools itself, as it does for anyone who uses `codex`, under the sandbox and approval settings of the request. Given up: Arbol filtering each request between the two | Decided 5 October 2026 by the owner: the proposed default (SYL-10) |
| CDX-D9 | Which level does a caller use for this route by default? | The caller's choice (DRV-D13) | Decided 6 October 2026 by the owner: there are no levels. Every run with tools is unrestricted, as in version 1 (DRV-D12, SYL-44) |
| CDX-D10 | Is the caller's message for a deny delivered to the agent some other way? | No. The tool has no place for it | Withdrawn 6 October 2026: nothing asks, so nothing is denied (SYL-67) |
| CDX-D13 | Which of the tool's other parts are switched on? | None in the first release. MCP servers, plug-ins and applications, memories, image generation, browser and computer use, hooks, skill search, tool suggestions and goals stay off, because each depends on something outside the request | Decided 6 October 2026 by the owner, against the proposed default: nothing of `codex` is switched off but its own memories, as the owner said later that day. Every other part is as the tool ships it (DRV-D26, SYL-71) |
