---
role: derived
---

# v1 Codex Driver inventory

Historical document-wide evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/server.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/rate_limit.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/images.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/system_prompt.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/notification_spool.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/tool_process.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/__main__.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/state_main.py`
- `arbol_deprecated_v1:drivers/codex/manifest.json`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/native_domain.py`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/provider_runtime.py`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/agent_attempt_execution.py`

Read: every file of `drivers/codex/arbol_driver_codex/`, `drivers/codex/manifest.json`, `pyproject.toml`, the PyInstaller spec and both launchd plist templates; the parts of `daemons/shared/arbol_shared/` those files depend on; the caller side in `daemons/core/arbol_core/orchestration/`; and every test that imports `arbol_driver_codex`. Commit `f2227d2` of `/Users/example/repos/sylvan-stack/arbol_deprecated_v1`; the working checkout has uncommitted changes (`git status --short` prints 1 line: untracked `renderer/storybook-static/`, outside the driver). Nothing of v1 was executed: no v1 code, no v1 test. The installed `codex-cli 0.159.2` was queried with `--help`, `features list` and `app-server generate-json-schema` only; no session, prompt, login or logout. Convention: historical evidence lists preserve `arbol_deprecated_v1:` paths and symbols as ordinary locators, not Source Ref declarations or provenance edges; documentation-corpus files (`/Users/example/Artifacts/arbol_deprecated_v1/…`), CLI output and the generated schema are named in prose.

## 1. Process and hosting
| Item | Value |
|---|---|
| Package / identity | `arbol-driver-codex` 0.1.0; `VERSION = "0.1.0"`, `DRIVER_NAME = "codex"`, `PROVIDER = "codex"` (provider family shared with `universe`; no code is imported from or by `drivers/universe` or `drivers/claude`) |
| Dependencies / binary | Python `>=3.11`, `aiohttp>=3.10,<4` (used only by the executor bridge), `arbol_shared`. PyInstaller onefile `arbol-driver-codex` built from `arbol_driver_codex/__main__.py`; the state build profile builds from `arbol_driver_codex/state_main.py` |
| Launch | launchd label `com.arbol.driver.codex` (a versioned template substitutes label, binary, socket name, build and instance id); `RunAtLoad`, `KeepAlive`, `ThrottleInterval` 10, `ProcessType` Background; no arguments. Environment: `HOME`, `PATH` (`…:$HOME/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`), `PYTHONUNBUFFERED=1`, `ARBOL_DRIVER_CODEX_SOCKET_NAME=driver.codex`, `ARBOL_PROVIDER_BUILD_ID`, `ARBOL_PROVIDER_INSTANCE_ID` |
| Socket / framing | Unix stream socket `<app support>/run/<name>.sock`, name from `ARBOL_DRIVER_CODEX_SOCKET_NAME` (default `driver.codex`); app support is `ARBOL_APP_SUPPORT` or `~/Library/Application Support/Arbol`; a stale path is unlinked, the new socket gets mode `0600`; on shutdown the file is removed only if it is still the inode this process bound. Framing: 4-byte big-endian length + UTF-8 JSON; envelope `kind` ∈ `hello`, `request`, `response`, `subscribe`, `event`, `unsubscribe`, `error`; requests on one connection run concurrently and are matched by `id`; a request envelope may also carry `dispatcher` and `attempt_authority` |
| Logging | `alog.setup("driver.codex")`: JSON lines to `<app support>/logs/driver.codex.log`, rotating 10 MiB × 5, level INFO; `rpc_in` / `rpc_out` records per request; launchd stdout/stderr go to `driver.codex.stdout.log` / `.stderr.log`. Loggers `arbol.ip.codex.turn`, `arbol.ip.codex.server` |
| Identity in health | `build_id` = `ARBOL_PROVIDER_BUILD_ID` or `dev`; `instance_id` = `ARBOL_PROVIDER_INSTANCE_ID` or `codex@<build_id>`; `execution` = `{provider_id:"codex", driver_id: ARBOL_PROVIDER_DRIVER_ID or "arbol_driver_codex", execution_id: fresh UUID per process (state host: the binding's incarnation id), generation: ARBOL_PROVIDER_GENERATION or "provider-r1", build_id, protocol_revision: 2}` |
| Manifest (`manifest.json`; `scripts/install.sh` writes the same to `<app support>/ip/codex/manifest.json`) | `name:"codex"`, `provider:"codex"`, `version:"0.1.0"`, `socket:"run/driver.codex.sock"`, `label:"Codex"`, `current:true`, `deprecated:false`, `default_for_provider:false`, `supports_failover_target:false`, `rate_limit_recovery_seconds:60` |

Entry points. Both first handle `--native-domain-worker` (the same binary doubles as the launchd worker for child processes, section 4), call `enter_native_service()`, `exit_if_import_selftest("arbol-driver-codex")` (exits 0 when `ARBOL_IMPORT_SELFTEST=1`), build `TurnRunner(codex_bin=CODEX_BIN or "codex")`, and serve under the startup guard `provider_retirement.startup("codex")` (refuses to bind when this instance id has a retirement marker or exit receipt).

| | `__main__.py` | `state_main.py` |
|---|---|---|
| Import boundary | none | `install_import_boundary()` forbids legacy modules, including `arbol_shared.turn_store`, so `server.py` cannot load |
| Binding | `configured_runtime("codex", …)`; with `ARBOL_STATE_RUNTIME_FILE` unset it opens Postgres read-only to confirm the authority mode is `legacy` and returns `None` | `require_binding_environment()` refuses without `ARBOL_STATE_RUNTIME_FILE`; `runtime is None` raises `StateRefused('state-only Provider requires a verified state authority binding')` |
| Served surface | the state runtime if a binding exists, else `server.build_handler()` + `server.build_stream_handler()` | `StateProviderRuntime.handle` only; no stream handler (a `subscribe` gets `streams not supported`) |

The same `TurnRunner.run(turn_id, params, emit)` runs under both hosts; only the envelope differs.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/__main__.py#main`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/state_main.py#main`
- `arbol_deprecated_v1:drivers/codex/manifest.json`
- `arbol_deprecated_v1:launchd/com.arbol.driver.codex.versioned.plist.in`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/socket_server.py#serve`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/ipc.py#encode`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/logging.py#setup`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_protocol.py#provider_execution_identity`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/provider_entrypoint.py#configured_runtime`

## 2. Wire surface
### 2.1 Legacy surface (`server.handle`)
| Method | Params read | Result | Errors (`ok:false`, `error`) | What it does |
|---|---|---|---|---|
| `ping` | none | `{pong:true}` | none | Liveness; public |
| `healthz` | none | `status:"ok"`, `version`, `uptime_seconds`, `pid`, `provider`, `build_id`, `instance_id`, `execution`, `turn_protocol:{version:2, capabilities}`, `codex_binary`, `codex_version` | none | Public. Capabilities: `els_attempt_observations_v1`, `els_attempt_commands_v1`, `els_attempt_launch_v1`, `dispatcher_commands_v1`, `quiescent_retirement_v1`, `witnessed_retirement_v1`, `launch_seal_v1`, `pinned_launch_v1`, `detached_execution`, `replay_since_seq`, `turn_attach`, `terminal_ack`, `feed_results_recovery`, `feed_permission_recovery`. `codex_version` is always `"unknown"` |
| `turn.execute` | `turn_id`, `chat_session_id`, `history`, `workspace_dirs`, `options`, `launch_protocol` (int `1`), `expected_execution` (the six identity fields, equal to this process); passes through `attempt_context`, `observation_protocol` | `{ok:true, turn_id, already_running, launch_receipt}` | `missing turn_id`; `Provider launch requires the pinned launch protocol`; `Provider launch requires a complete execution identity`; `Provider launch execution identity changed`; `attempt launch request differs from retained receipt`; `attempt replay was collected; launch cannot be repeated`; `receiver launch admission is sealed`; retirement refusals | Runs `gc_completed`, then starts one detached task per `turn_id` (`TurnStore.start_once`). `launch_receipt` = SHA-256 of the canonical JSON of all params except `attempt_authority`. A repeat with the same receipt returns `already_running:true` and starts nothing |
| `turn.cancel` | `turn_id` | `{ok:true}` | none | `runner.cancel` then `store.cancel` (section 10) |
| `turn.feed_results` / `turn.feed_permission` | `turn_id`, `batch_id`, `results` / `turn_id`, `ask_id`, `behavior` (default `deny`) | `{ok:true}` / `{ok:false}` always | none | No-ops; `resolve_wait` is never reached |
| `turn.permission_waits` / `turn.admit_permission_waits` / `turn.release_permission_admission` | `turn_id`; `ask_ids`; `admission_token` | `{ask_ids:[]}` / `{admitted:false, admission_token:null}` / `{ok:false}` | none | No-ops |
| `turn.inventory` | (wrapper: `participant_challenge`) | identity fields, `pid`, `turns[]`, `running`, `unacknowledged_terminal`, plus admission status merged in by the wrapper | none | Section 11 |
| `turn.describe` / `turn.attach` / `turn.ack` | `turn_id`; + `since_seq`, `core_generation`; + `terminal_seq` | section 11 | `missing turn_id`; `str(exc)` on bad integers | Section 11 |
| `turn.admission.status`, `turn.admission.seal`, `turn.deployment.census`, `turn.retirement.prepare`, `turn.retirement.status` | shared deployment protocol | store admission status | e.g. `receiver admission identity mismatch` | Shared receiver sealing/retirement; not Codex-specific |
| anything else | | | `unknown method: <name>` | |

Envelope added by `build_handler()` (`authenticated_handler`): only `ping` and `healthz` are public. Every other request needs a valid `dispatcher` grant and (except the instance methods) a bounded string `turn_id`; any `CredentialError`, `AdmissionSealed`, `ValueError` or `OSError` raised inside the wrapper is flattened to the single text `Provider dispatcher authority refused`. For a `turn_id` the store does not retain, every method other than `turn.execute`, `turn.recover` and the instance methods gets that text, so the raw handler's `found:false` replies are not reachable through the wrapper. The wrapper also implements two methods the raw handler lacks: `turn.recover` (result `{attempt_id, recovered, historical}` or `{attempt_id, disposed:true, terminal_seq}`) and `turn.cleanup` (params `turn_id`, `terminal_seq`; result `{disposed:true, terminal_seq}`); `turn.ack` returns `{found, acknowledged, terminal_seq, disposed:true}` once a disposition is pending. The five mutation methods (`turn.cancel`, `turn.feed_results`, `turn.feed_permission`, `turn.admit_permission_waits`, `turn.release_permission_admission`) run joined under `TurnStore.mutate`, so a dropped connection cannot abandon them.

Stream: `turn.events`, params `turn_id` (required) and `since_seq` (default 0). Replays buffered events with `seq > since_seq`, then tails live events, and ends after `done`. Raw-handler stream errors are events named `error`: `{message:"missing turn_id in subscribe params"}`, `{message:"unknown stream: <name>"}`. Under `authenticated_stream` each emission is separately authorised with a 10 s send timeout; a refusal ends the stream with an `error` frame carrying `Provider dispatcher authority refused`.

### 2.2 State surface (`StateProviderRuntime.handle`)
| Method | Params | Result / effect |
|---|---|---|
| `healthz` | none | `status:"ok"`, `state_provider_protocol:1`, `provider`, `store_id`, `pid`, `database_id`, `authority_epoch`, `storage`, identity with capabilities `quiescent_retirement_v1`, `witnessed_retirement_v1`, `state_checkpoints_v1` |
| `state.deliver` | `attempt_id`, `command_id`, `request_digest`, `action` ∈ `launch`, `admit` | `launch`: builds params `{chat_session_id, turn_id: attempt_id, history, workspace_dirs, options, output_contract:"state-checkpoints-v1"}` from the accepted submission and starts `runner.run`; result `{registered, attempt_id, store_id, binding}`. `admit`: cancel → `runner.cancel` + task cancel, result `{cancel_requested, attempt_id}`; a `native_permission` decision → `runner.feed_permission` (returns `False`, so refused with `permission delivery was not confirmed; reconciliation required`); `results` → `runner.feed_results` |
| `state.checkpoint` / `state.acknowledge` | `attempt_id`; + `result` | Blocks for the next pending checkpoint / releases it after database read-back (section 11) |
| `state.cleanup` | `attempt_id`, `command_id`, `request_digest` | `{pending_cleanup:true}` while the task runs; refuses `runner termination is not confirmed` / `native execution resources remain unaccounted`; else records `dispose` |
| `turn.inventory`, `turn.retirement.prepare`, `turn.retirement.status` | `participant_challenge`, … | State-backed inventory and retirement |
| other | | `unsupported state Provider method`. There is no `ping` and no stream |

### 2.3 Events the driver emits
Every payload carries `turn_id`. In the legacy host `TurnStore` adds `_ip_seq` (per turn, starting at 1) inside the data payload.

| Event | Payload fields | Emitted when |
|---|---|---|
| `assistant_text_delta` | `text` | Once per completed `agentMessage` item: the whole text, stripped; empty text is skipped |
| `assistant_thinking_delta` | `text` | Once per completed `reasoning` item: `summary` strings joined with `\n`, stripped; empty skipped |
| `native_tool_invoked` | `tool_use_id`, `tool_name`, `input` | `item/started` of `commandExecution` (`tool_name:"Bash"`, `input:{command}`) or `fileChange` (`tool_name:"ApplyPatch"`, `input:{changes}`) |
| `native_tool_settled` | `tool_use_id`, `ok`, and `result` (when `ok`) or `error` (when not) | `item/completed` of the same two item types |
| `usage` | `model` (the requested model), `input_tokens`, `output_tokens`, `cost_usd: null` | Every `thread/tokenUsage/updated` notification |
| `error` | `message` | Validation, image or startup failure, or a fatal Codex message that is not a rate limit (cut to 1024 characters) |
| `cycle_complete` | `cycle_n: 1`, `discard: false` | Once, after the notification loop ended normally or with a fatal message. Not emitted on validation/image/startup failure, on cancel, or when the loop raises |
| `rate_limited` | `reason` (≤200 characters), optional `recovery_hint_seconds` | After `cycle_complete` when the fatal message classified as a rate limit |
| `done` | `reason` ∈ `no_more_requests`, `error`, `rate_limited`, `cancelled` | Terminal, last event |

`tool_use_id` is `codex-<32 hex>-<Codex item id>`; the hex part is a fresh `uuid4` per `_run_one_cycle`, so a retry of the same turn produces different ids. Orders pinned by tests: success `native_tool_invoked, native_tool_settled, assistant_text_delta, usage, cycle_complete, done`; rate limit `cycle_complete, rate_limited, done`; fatal `error, cycle_complete, done`; startup failure `error, done`. Host backstops: if the runner raises, `TurnStore._supervise_run` publishes `error {turn_id, message: str(exception)}` and `done {reason:"error"}`; if the task is cancelled, `done {reason:"cancelled"}`; if the runner returns without a terminal, `done {reason:"no_more_requests"}`. The state host does the same in `StateProviderRuntime._run`. The driver never emits `arbol_request_batch`, `native_permission_ask`, `native_permission_ask_cancelled` or `continuation_nudge`.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/server.py#handle`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/server.py#stream`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_authority.py#authenticated_handler`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_authority.py#authenticated_stream`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_launch.py#launch_receipt`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_protocol.py#BASE_CAPABILITIES`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore._supervise_run`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/provider_runtime.py#StateProviderRuntime.handle`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/provider_runtime.py#StateProviderRuntime._deliver`
- `arbol_deprecated_v1:tests/unit/test_codex_cli_turn.py`

## 3. Turn options
| Top-level key | Type | Effect |
|---|---|---|
| `chat_session_id` | string | Must be non-empty, else `error` `missing chat_session_id or workspace_dirs`. Not used otherwise |
| `workspace_dirs` | list of paths | Must be non-empty (same error). `[0]` is the app-server cwd, the thread `cwd`, the environment `cwd` and the only `runtimeWorkspaceRoots` entry. All entries are listed in the system prompt; entries after the first reach Codex in no other way |
| `history` | list of `{role, content, attachments?}` | Must be non-empty and end with `role:"user"`, else `error` `history must end with a user message`. Rendered into one prompt (section 6) |
| `options` | object, default `{}` | Below |
| `output_contract` | string | Exactly `state-checkpoints-v1` disables the 200 KiB truncation of tool results/errors; set only by the state host. (`turn_id` is read by the host, not by the runner body) |

| `options` key | Set by caller | Read by driver | Values / default | Effect |
|---|---|---|---|---|
| `model` | per-message override, else the route's `default_model` | yes | default `DEFAULT_MODEL = "gpt-5.5"` | Sent as `model` on `thread/start` and `turn/start`; echoed in every `usage` event |
| `thinking_level` | when not `none` | yes | mapping in section 6; default absent | Sent as `effort` on `turn/start`, or omitted |
| `additional_instructions` | session decisions and extra instructions joined with a blank line | yes | string | Appended to the prompt after the system prompt |
| `session_decision_instructions` | composed, then popped and folded into `additional_instructions` by `_run_one_attempt` before the first launch | yes | string | Appended before `additional_instructions` when present. Absent on the first legacy launch; present on the legacy relaunch after an auth error, which rebuilds options without popping |
| `full_permissions`, `provider_base_url` | from route settings | **no** | bool, string | None (section 8) |
| `fast_mode` | `true` when the chat has fast mode and the route's provider is `codex` | **no** | bool | None; no service tier is sent |
| `oauth_token`, `account_id` | when the bound Subscription is `logged_in` and its stored blob has them (legacy path) | **no** | strings | None; not injected anywhere |

`_env_overrides_for(options)` accepts `options` and ignores it. There is no working-directory option beyond `workspace_dirs`, no continuity field (no thread id, no resume token), and no limit option (max turns, timeout, token budget).

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner.run`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#render_prompt`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/agent_attempt_execution.py#AgentAttemptExecutionService.compose_turn_options`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/agent_attempt_execution.py#AgentAttemptExecutionService._run_one_attempt`
- `arbol_deprecated_v1:tests/unit/test_codex_permission_options.py`

## 4. App-server process
Two Codex processes per turn, both from the same pinned executable; neither is shared between turns and nothing is kept warm.

| | Control (app-server) | Executor (exec-server) |
|---|---|---|
| argv | `<codex> app-server --listen stdio:// -c notify=[]`, then `-c features.<name>=false` for each of the 27 `DISABLED_FEATURES` and `-c features.<name>=true` for each of the 2 `ENABLED_FEATURES` | `<codex> exec-server --listen stdio` |
| Started by | `TurnRunner._launch_process` → `native_domain.launch`: a one-shot launchd job `gui/<uid>/dev.arbol.native.<nonce>` whose worker (`--native-domain-worker`) runs `subprocess.Popen(argv, cwd, env, close_fds=True)` after an authenticated handshake; stdio travels over four Unix-socket channels (`control`, `stdin`, `stdout`, `stderr`) at `/private/tmp/arbol-nd-<nonce>/control.sock` | `tool_process.launch` → `asyncio.create_subprocess_exec(…, start_new_session=True)`: a direct child of the driver in its own session |
| When / cwd | First, before any protocol traffic; cwd `workspace_dirs[0]`, resolved strictly | After `thread/start` succeeded; same resolved directory |
| Environment | turn environment + `CODEX_EXEC_SERVER_URL=none` | turn environment |
| Ownership | Its own kernel RESOURCE coalition (not a child or process group of the driver); journalled under `<app support>/run/native-domains/<nonce>/` | Direct child only; commands it starts are deliberately outside Arbol's cleanup |
| Stop | `launchctl bootout`, then signal every coalition member: `SIGTERM` for the first 2 s, `SIGKILL` after, polling every 0.05 s, until the coalition is gone or 15 s elapsed (`native descendant retirement remains unresolved`) | Close stdin; wait 1 s; `terminate()` the direct child; wait 1 s; `kill()`. Never signals the process group or descendants |

Turn environment: `{**os.environ, **_env_overrides_for(options)}` minus `ARBOL_LIFECYCLE_APPROVAL_SOCKET`. The only overlay is `PATH`, extended at the end with `~/bin` and `/opt/homebrew/bin` when each exists as a directory and is not already listed. No `HOME`, `CODEX_HOME`, token, API-key or proxy variable is set, removed or rewritten. `start_new_session=True` is passed to `native_domain.launch`, which does not use the argument.

Executable resolution (`resolve_executable(CODEX_BIN or "codex")`, on `PATH`): if the resolved path is `…/bin/codex.js`, read `../package.json` (≤65536 bytes; `name` `@openai/codex`, `version` `0.159.2`) and use `node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex`; the JavaScript launcher is never run. The native binary must be a regular executable file, not group/other-writable, exactly `EXECUTABLE_BYTES` long with SHA-256 `EXECUTABLE_SHA256`. Its sibling `codex-code-mode-host` must be a canonical regular file, mode exactly `0755`, owned by uid 0 or the current uid, `HOST_BYTES` long with SHA-256 `HOST_SHA256`; the parent directory must not be named `MacOS` or `codex-resources`, and no `codex-resources/codex-code-mode-host` may exist beside it (or beside the parent of a `bin` directory).

Start sequence (every request uses the 30 s default timeout): `initialize` → notification `initialized` → `config/read` → `configRequirements/read` → validation (section 5) → `thread/start` → start executor and bridge → `environment/add` → `environment/info` → `environment/status` (must be `ready`) → `turn/start`. Payloads are in section 6.

Executor bridge (`OwnedExecutor`): an aiohttp WebSocket listener on `127.0.0.1` port 0, path `/<64-hex secret>`; the URL `ws://127.0.0.1:<port>/<secret>` is handed to the app-server in `environment/add`. Exactly one attachment; a request with an `Origin` header, a query string or a wrong secret gets HTTP 403. Each text frame from the app-server is validated and forwarded as one JSON line to the exec-server's stdin; each stdout line is validated and sent back. Allowed request methods: `initialize`, `initialized`, `environment/info`, `environment/status`, `process/start`, `process/read`, `process/write`, `process/signal`, `process/terminate`, `fs/readFile`, `fs/open`, `fs/readBlock`, `fs/close`, `fs/writeFile`, `fs/createDirectory`, `fs/getMetadata`, `fs/canonicalize`, `fs/readDirectory`, `fs/walk`, `fs/remove`, `fs/copy`. Allowed exec-server notifications: `process/output`, `process/exited`, `process/closed`. Refused: `initialize` with `resumeSessionId` or a second `initialize`; any request before `initialized`; `process/start` carrying `sandbox`, `managedNetwork`, `networkProxy`, `enforceManagedNetwork` or `shellSnapshot`; an `fs/*` request whose `sandbox` context is present with `permissions` other than `{type:"external", network:"enabled"}`; more than 32 pending requests; duplicate JSON keys; frames over 8 MiB. `initialize` / `environment/info` results must report `executorVersion` `0.159.2` and `platformOs` `macos`; the bridge rewrites six capabilities to `false` (`networkProxyLaunch`, `capabilityDiscoverySandbox`, `capabilityDiscoveryV2`, `environmentConfigRead`, `httpHeaderEnvVars`, `shellSnapshotV2`). Any violation fails the executor, and the next `executor.check()` in `Session.events` raises.

Shutdown order (`Session._cleanup`, run once after the notification loop and again, idempotently, from the runner's `finally`): control process cleanup, executor cleanup, `AppServer.close()` (cancels and joins the stdout/stderr readers), then the direct-exit waiter. Errors are collected and re-raised as `RuntimeError('Codex native session cleanup remains unresolved')`. No shutdown request is sent to the app-server; it is stopped by signal.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#control_argv`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session._cleanup`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#_env_overrides_for`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#resolve_executable`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#_verify_code_mode_host`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#OwnedExecutor`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/tool_process.py#ToolProcess._cleanup`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/native_domain.py#launch`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/native_domain.py#NativeProcess._cleanup`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/native_domain_worker.py#run`

## 5. Configuration validation
Every refusal below is raised inside `Session.start` and reaches the caller as one `error` event with message `Codex owned execution could not start: <text>` followed by `done {reason:"error"}`. The saved configuration is never edited. `<home>` is `CODEX_HOME` if set, else `HOME/.codex`, both taken from the turn environment.

| # | When checked | Condition | Exact text |
|---|---|---|---|
| 1 | before launch | any of `CODEX_EXEC_SERVER_NOISE_REGISTRY_URL`, `…_ENVIRONMENT_ID`, `…_AUTH_TOKEN`, `…_CHATGPT_ACCOUNT_ID` is non-empty | `Inherited Codex remote environment configuration conflicts with the owned executor` |
| 2 | before launch | `CODEX_HOME` set but not an absolute path string; `CODEX_HOME` unset and `HOME` missing, empty or not absolute | `Arbol native Codex requires an absolute CODEX_HOME`; `Arbol native Codex requires an absolute HOME when CODEX_HOME is unset` |
| 3 | before launch | `<home>/environments.toml` exists or is a (dangling) symlink | `Arbol native Codex requires no saved environments.toml; its executor is fixed per turn` |
| 4 | before launch | `<home>/.env` exists or is a symlink | `Arbol native Codex cannot apply .env startup overrides to its fixed executor environment` |
| 5 | before launch | executable not on `PATH`; npm `package.json` over 65536 bytes; npm name or version differs | `Codex 0.159.2 native executable is unavailable`; `unsupported Codex package metadata`; `Codex package version differs from the verified adapter` |
| 6 | before launch | binary type, mode or size differs; hash differs or the file changed while hashing | `Codex executor executable identity is unsupported`; `Codex executor executable bytes changed` |
| 7 | before launch | code-mode host checks (six texts) | `Codex code-mode host executable is unavailable`; `Unsupported Codex code-mode host installation layout`; `Codex code-mode host resource redirection is unsupported`; `Codex code-mode host must be its canonical sibling`; `Codex code-mode host executable identity is unsupported`; `Codex code-mode host executable bytes changed` |
| 8 | after `config/read` | `config` is not an object, or `requirements` is neither null nor an object | `Codex effective configuration is unavailable` |
| 9 | after `config/read` | `model_provider` is not null/`openai`, or `model_providers` is non-empty | `Arbol native Codex currently requires the built-in OpenAI provider` |
| 10 | after `config/read` | `permissions`, `default_permissions` or `network` is non-empty | `Arbol native Codex cannot represent the configured permission/network profile` |
| 11 | after `configRequirements/read` | requirements `network`, `hooks` or `defaultPermissions` is non-empty | `Arbol native Codex cannot represent the managed execution requirements` |
| 12 | after `config/read` | `features` is not an object, a disabled feature is not exactly `false`, or an enabled feature is not exactly `true` | `Codex did not apply the fixed Arbol execution feature profile` |
| 13 | after `configRequirements/read` | `featureRequirements[<disabled feature>]` is `true`; `featureRequirements[<enabled feature>]` is `false` | `A managed Codex feature conflicts with the fixed Arbol executor`; `A managed Codex requirement disables the fixed Arbol executor` |
| 14 | after `config/read` | `notify` is neither null nor `[]` | `Codex notification commands are unsupported in this executor` |
| 15 | after `config/read` | `mcp_servers` is not an object or has more than 128 entries; a name does not match `[A-Za-z0-9_-]{1,128}` | `Unsupported Codex MCP configuration`; `Unsupported Codex MCP server name` |
| 16 | after `thread/start` | no string `thread.id` in the result | `Codex did not return its new thread identity` |
| 17 | executor start | owner, env or policy contract violated; cwd differs; attempt already retained | `invalid fixed executor launch contract`; `executor cwd differs from the captured policy workspace`; `Codex executor attempt is already retained` |
| 18 | after `environment/status` | `status` is not `ready` | `Codex owned execution environment is not ready` |
| 19 | after `turn/start` | no string `turn.id` in the result | `Codex did not return its active turn identity` |

Saved MCP servers are not a refusal: each is switched off for the thread with `mcp_servers.<name>.enabled = false`. `validate_config` returns the per-thread overrides `{notify: [], features.<name>: false|true …, mcp_servers.<name>.enabled: false …}`. An empty exception text is replaced by the exception type name. Requirements such as `allowedApprovalPolicies`, `allowedSandboxModes`, `allowedLoginMethods` and `modelProvider` (present in the 0.159.2 schema) are not examined.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#validate_config`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#codex_home`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#resolve_executable`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#_verify_code_mode_host`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#start_executor`
- `arbol_deprecated_v1:tests/unit/test_codex_session.py`

## 6. Protocol use
Transport: newline-delimited JSON over the app-server's stdio. Outgoing records carry no `jsonrpc` member; request ids are integers counting from 1 per app-server process; at most 32 requests pending; a frame is at most 8 MiB in either direction; `NaN`/`Infinity` are rejected. A response whose `result` is not an object, a response for an unknown id, a response with both or neither of `result`/`error`, or a notification whose `params` is not an object fails the whole transport. An `error` response rejects that request with `ProtocolError(error.message or 'Codex app-server request failed')`. A request timeout fails the whole transport (`Codex app-server request timed out`).

| # | Direction | Name | Payload sent / fields used |
|---|---|---|---|
| 1 | request, then notification | `initialize`, `initialized` | `clientInfo:{name:"arbol", title:"Arbol", version:"0.1.0"}`, `capabilities:{experimentalApi:true}`, result ignored; then `initialized` with `{}` |
| 2 | requests | `config/read`, `configRequirements/read` | `cwd: workspace_dirs[0]`, `includeLayers:false`, uses result `config`; then `{}`, uses result `requirements` |
| 3 | request | `thread/start` | `cwd`, `model`, `ephemeral:true`, `environments:[]`, `approvalPolicy:"never"`, `sandbox:"danger-full-access"`, `config:<overrides from section 5>`, `developerInstructions:"This Arbol native executor supports shell and filesystem tools. Browser automation, desktop automation, local MCP servers, plugins, hooks and subagents are unavailable in this execution profile."`; uses result `thread.id` |
| 4 | request | `environment/add` | `environmentId:"arbol-<32 hex>"`, `execServerUrl`, `connectTimeoutMs:10000` |
| 5 | request | `environment/info`, `environment/status` | `environmentId`; `info` result ignored, `status` result field `status` used |
| 6 | request | `turn/start` | `threadId`, `model`, `approvalPolicy:"never"`, `sandboxPolicy:{type:"externalSandbox", networkAccess:"enabled"}`, `environments:[{environmentId, cwd, runtimeWorkspaceRoots:[cwd]}]`, `input:[{type:"text", text:<prompt>}, {type:"localImage", path}…]`, and `effort` only when mapped; uses result `turn.id` |
| 7 | server request | `item/commandExecution/requestApproval`, `item/fileChange/requestApproval` | answered `{decision:"decline"}` |
| 8 | server request | `item/permissions/requestApproval` | answered `{permissions:{}, scope:"turn"}` |
| 9 | server request | any other method | answered with error `{code:-32601, message:"Arbol does not support this Codex client request"}` |
| 10 | notification in | `item/started`, `item/completed` | `item.type`, `item.id`, and per type the fields in section 7 |
| 11 | notification in | `thread/tokenUsage/updated` | `tokenUsage.last.inputTokens`, `tokenUsage.last.outputTokens` |
| 12 | notification in | `error` | `willRetry`, `error.message` |
| 13 | notification in | `turn/completed` | `turn.id`, `turn.status`, `turn.error.message` |
| 14 | notification in | every other method | queued, then ignored (no mapping) |

Never sent: `turn/interrupt`, `turn/steer`, `thread/resume`, `thread/fork`, any `account/*`, `model/list`, any `mcpServer/*`. Server requests are answered inside the reader and are not queued as events. Each notification's `params.threadId` and `params.turnId`, when present, must equal the thread and turn this session created, otherwise the loop raises `Codex notification belongs to another thread` / `… another turn`.

Thread, turn and continuity: one new `ephemeral` thread and exactly one `turn/start` per Arbol attempt; nothing is resumed. Earlier conversation reaches Codex only through the prompt text. `render_prompt` joins with blank lines: (1) the system prompt: template `codex-native.md.tmpl` with `$workspace_dirs`, then `workspace-boundary.md.tmpl`, then the fixed block `## Protected Arbol lifecycle operations` plus every `.md`/`.markdown` file of the shared and repository `system-instructions` chapters, then `code-navigation.md.tmpl` when a workspace directory is inside or contains `ARBOL_KN_CODE_ROOT`; templates are read from `<ARBOL_ARTIFACTS_ROOT or ~/Artifacts>/<ARBOL_SYSTEM_INSTRUCTIONS_REPO or Arbol>/system-instructions/` on every turn, and a missing or empty template raises; (2) `session_decision_instructions`; (3) `additional_instructions`; (4) `## Earlier conversation in this Chat Session` with one `user: …` / `assistant: …` paragraph per earlier history row whose role is `user` or `assistant` and whose content is a non-blank string (other rows are dropped); (5) `## Current request` with the last row's content, or `(no user message)`. Codex's own base instructions stay in place; `baseInstructions` is not sent.

| `thinking_level` | `minimum` | `low` | `medium` | `high` | `xhigh` | `max` | `ultra` | `none`, empty, unknown |
|---|---|---|---|---|---|---|---|---|
| `effort` sent | `low` | `low` | `medium` | `high` | `xhigh` | `xhigh` | `xhigh` | omitted |

Model fallback: the only fallback is `DEFAULT_MODEL` when `options.model` is empty. The model is not checked against a model list, `allowProviderModelFallback` is not sent, and `model/rerouted` is ignored, so `usage.model` is always the requested name.

Images: for every `user` history row, each attachment must be `{type:"image", mime_type, data}` with `mime_type` ∈ `image/png` (`.png`), `image/jpeg` (`.jpg`), `image/webp` (`.webp`), `image/gif` (`.gif`) and strict base64 `data`. Each is written to `image-<n><suffix>` (n counts across the whole history; attachment names are ignored) in a per-turn `tempfile.TemporaryDirectory(prefix="arbol-codex-images-")`; the row's text gains `[Attached image <n>]` lines; the paths are sent as `localImage` inputs in the same order. Images of earlier rows are attached again on every turn. Errors, before any process starts: `unsupported Codex attachment type`, `unsupported Codex image MIME type`, `Codex image attachment has invalid base64 data`, `Codex image attachment is empty`. The directory is removed only after process cleanup succeeded.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#AppServer.request`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#AppServer._dispatch`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#render_prompt`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#effort_for_thinking`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/system_prompt.py#render_codex_system_prompt`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/images.py#prepare_images`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/system_instructions.py#render_instruction_template`

## 7. Output mapping
Two steps: `exec_events` rewrites an app-server notification into the older `codex exec --json` record shape, then `map_exec_event` turns that record into `(kind, payload)` and `_run_one_cycle` emits the Arbol event.

| App-server notification | Condition | Arbol event(s) |
|---|---|---|
| `item/started`, item `commandExecution` | | `native_tool_invoked` `{tool_name:"Bash", input:{command: item.command}}` |
| `item/started`, item `fileChange` | | `native_tool_invoked` `{tool_name:"ApplyPatch", input:{changes: item.changes}}` |
| `item/completed`, item `agentMessage` | stripped `text` non-empty | `assistant_text_delta` |
| `item/completed`, item `reasoning` | `"\n".join(summary)` non-empty after strip | `assistant_thinking_delta` (`content` is not used) |
| `item/completed`, item `commandExecution` | `ok` = `exitCode == 0`, or when `exitCode` is null `status == "completed"` | `native_tool_settled`: `ok:true, result: aggregatedOutput`, or `ok:false, error:` trimmed output, else `command <status or "failed">`, plus ` (exit code N)` for a non-zero code |
| `item/completed`, item `fileChange` | `status` `declined` is first rewritten to `failed`; `ok` = `status != "failed"` | `native_tool_settled`: `result` or `error` = change summary; for a path-keyed object `<path>: <kind>` joined with `; `, otherwise `str(changes)` |
| `item/completed`, item type `error` | (no such item type in the 0.159.2 schema) | log warning only, first 300 characters |
| `item/started` of any other type; `item/completed` of other types (`mcpToolCall`, `webSearch`, `plan`, …) | | none |
| `thread/tokenUsage/updated` | | `usage` `{input_tokens: last.inputTokens, output_tokens: last.outputTokens, cost_usd: null}` |
| `error` | `willRetry` false / true | fatal with `error.message` or `Codex turn failed` / none |
| `turn/completed` | `status` `failed` | fatal with `turn.error.message` or `codex turn failed` |
| `turn/completed` | `status` `completed` | loop ends; then `cycle_complete`, `done {reason:"no_more_requests"}` |
| `turn/completed` | `status` `interrupted` / any other status / `turn.id` differs | raises `Codex interrupted the active turn` / `Unsupported Codex terminal status` / `Codex terminal identity differs from the active turn` |
| `item/agentMessage/delta`, `item/reasoning/*Delta`, `item/commandExecution/outputDelta`, `turn/started`, `thread/started`, `account/*`, `model/rerouted`, … | | none |

Partial output: none. Text and reasoning arrive only as whole completed items, command output only at settlement. Final result: there is no separate result event; the assistant text is whatever `assistant_text_delta` events were emitted, sealed by `cycle_complete`. A fatal message stops the loop at once; later notifications are not read. In the legacy host `result` (when a string) and `error` are cut to 200 × 1024 characters unless `output_contract` is `state-checkpoints-v1`. Usage: only `tokenUsage.last` input and output counts; cached, cache-write, reasoning and total counts and `tokenUsage.total` are dropped; one `usage` event per notification, which the caller sums within an attempt.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#exec_events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#map_exec_event`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#_item_events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#usage_from`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/ip_events.py#IpEventsMixin`
- `arbol_deprecated_v1:tests/unit/test_codex_app_server.py`

## 8. Tools and permissions
| Topic | v1 behaviour |
|---|---|
| Approval policy | `approvalPolicy:"never"` on both `thread/start` and `turn/start`, always |
| Sandbox | `sandbox:"danger-full-access"` on the thread; `sandboxPolicy:{type:"externalSandbox", networkAccess:"enabled"}` on the turn; `tool_policy` ignores its `sandbox`, `network` and `env` arguments and always returns `CodexToolPolicy("danger-full-access", <workspace>, network_access=True)`. Arbol applies no sandbox of its own |
| Arbol "Full permissions" | No effect. `options.full_permissions` is never read; `test_full_permissions_reaches_spawned_cli` pins identical requests for `true` and `false`, also with `ARBOL_CODEX_SANDBOX=read-only` and `ARBOL_CODEX_NETWORK=false` set |
| Approval requests from Codex | Never shown to the Leather Bag and never forwarded to the caller: command and file-change approvals get `decline`, a permissions request gets an empty grant, every other server request gets error `-32601` (section 6) |
| Tool surface | On: shell and file tools through the owned exec-server, with `unified_exec` and `code_mode_host` forced on. Off: the 27 `DISABLED_FEATURES` (`shell_snapshot`, `shell_snapshot_v2`, `hooks`, `code_mode`, `code_mode_only`, `code_mode_prewarm`, `multi_agent`, `multi_agent_v2`, `apps`, `plugins`, `remote_plugin`, `browser_use`, `browser_use_external`, `browser_use_full_cdp_access`, `computer_use`, `in_app_browser`, `in_app_chat`, `in_app_dictation`, `in_app_local_automation`, `image_generation`, `memories`, `workspace_dependencies`, `skill_mcp_dependency_install`, `executor_capability_discovery`, `deferred_executor`, `network_proxy`, `request_permissions_tool`), every saved MCP server, and `notify` |
| `tool_process.py` | `launch()` starts the exec-server as a plain child; `ToolProcess._cleanup()` reaps only that child and returns the receipt `{evidence:"direct-executor-reaped", pid, returncode}`; `retired()` checks the receipt against the process. Commands the exec-server started keep running after the turn (pinned by `test_detached_http_server_survives_executor_cleanup`) |
| `notification_spool.py` | `NotificationSpool`: ordered queue of notifications between the stdout reader and the single consumer, so a slow consumer cannot block request replies. Backed by `SpooledTemporaryFile` (1 MiB in memory, then an anonymous disk file, no upper bound); `full()` is always `False`; consumed prefixes are reclaimed when empty or once 4 MiB has been read; `close()` discards everything |
| `feed_results` / `feed_permission` / waits | No-op / returns `False`; the driver emits neither a request batch nor a permission ask, so there is nothing to answer. `permission_wait_ids` → `[]`; `admit_permission_waits` → `None`; `release_permission_admission` → `False` |
| Observation / `ipc_paths` | Tool calls are observed after the fact only (`native_tool_invoked` / `native_tool_settled` for commands and patches). `ipc_paths` is always `()`; no Arbol socket is granted to the Codex processes, and `ARBOL_LIFECYCLE_APPROVAL_SOCKET` is stripped from their environment |

The documentation corpus agrees (`product-spec/06-tools-and-permissions.md`, Codex row) with one refinement: it says remaining approval requests are "declined automatically", while only two request types get a `decline`; a permissions request gets an empty grant and all others a method-not-found error. The agent-facing template in the corpus (`system-instructions/codex-native.md.tmpl`) says Arbol inherits the CLI's configuration, that Full Permissions applies to native tools and that protected lifecycle actions need a dedicated approval; the code contradicts all three.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#tool_policy`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#DISABLED_FEATURES`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#AppServer._dispatch`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/tool_process.py#ToolProcess`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/notification_spool.py#NotificationSpool`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner`
- `arbol_deprecated_v1:tests/unit/test_codex_cli_turn.py`
- `arbol_deprecated_v1:tests/unit/test_codex_tool_process.py`

## 9. Credentials and login state
- The turn runs under whatever login the installed Codex CLI already holds for the OS account running the driver. The driver injects no token, sets no `CODEX_HOME`/`HOME`, sends no `account/*` request, and reads no credential file. The only files it inspects under the Codex home are `environments.toml` and `.env`, and only for existence.
- `options.oauth_token` and `options.account_id`, which the legacy caller fills from the bound Subscription's stored blob, are ignored. In the state host `ProviderCredentials.options` returns the options untouched when the binding mode is `native_cli` (and refuses `native CLI credential binding differs from the accepted Provider` unless the driver id is `arbol_driver_codex` and the provider is `codex`); the root side grants that mode to the `codex` route with a `codex` Subscription without requiring `auth_state == "logged_in"`.
- Consequence (inferred): the Subscription bound to this route only attributes usage and selects the model catalogue on the root side; this driver cannot tell two accounts apart. The driver environment passes through unchanged, so any `OPENAI_API_KEY`, `CODEX_API_KEY` or `CODEX_ACCESS_TOKEN` present in the launchd environment would reach Codex (inferred; the plist templates set none).
- Login failure detection is text-only, on a fatal message: lower-cased substring match against `AUTH_ERROR_INDICATORS` = `not logged in`, `logged out`, `codex login`, `401`, `unauthorized`, `invalid api key`, `missing credentials`, `please login`, checked after the rate-limit and model-version checks. Report: `error` whose message is the Codex text plus ` — the codex CLI uses its own login; run `codex login` and retry`, then `cycle_complete`, `done {reason:"error"}`. No `authentication_error` flag, no login-state event, no refresh. `codexErrorInfo` (for example `unauthorized`) is not read.
- The caller's relaunch-after-auth-error path keys on `codex responses http 401` / `token_expired` (`universe` texts) or the Claude markers. The hint this driver appends matches none of them, so a relaunch happens only if Codex's own text contains such a marker; it would then re-import a root-side credential this driver does not use.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#_env_overrides_for`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/rate_limit.py#AUTH_ERROR_INDICATORS`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/credentials.py#ProviderCredentials.options`
- `arbol_deprecated_v1:daemons/core/arbol_core/state_intake.py#StateTurnIntake._credentials`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/support.py#_is_codex_auth_error`
- `arbol_deprecated_v1:tests/state/test_intake_policy.py`

## 10. Failures, limits and cancel
Fatal message classification, in this order (first match wins; all are case-insensitive substring tests on the message text):

| Order | Class | Patterns | Result |
|---|---|---|---|
| 1 | rate limit | `RATE_LIMIT_INDICATORS`: `rate limit`, `rate_limit`, `429`, `too many requests`, `usage limit`, `usage cap`, `insufficient_quota`, `quota`, `limit reached`, `you've hit your`, `you have hit your`, `weekly limit`, `daily limit` | no `error` event; `cycle_complete`, `rate_limited {reason: message[:200], recovery_hint_seconds?}`, `done {reason:"rate_limited"}` |
| 2 | model too new for the CLI | `requires a newer version of codex`, `requires a newer version of the codex` | `error`: message + ` — the installed codex CLI (version unknown) cannot run this model; upgrade it (`codex update`) or pick another model` |
| 3 | login | section 9 | `error`: message + login hint |
| 4 | other | | `error`: message as is |

`recovery_hint_seconds` (`extract_recovery_seconds`): the first match of `retry\s+in\s+(\d+)\s*(?:s|sec|seconds?)\b`, `try\s+again\s+in\s+(\d+)\s*(?:s|sec|seconds?)\b`, `wait\s+(\d+)\s*(?:s|sec|seconds?)\b` gives seconds; otherwise `retry\s+in\s+(\d+)\s*(?:m|min|minutes?)\b` or `try\s+again\s+in\s+(\d+)\s*(?:m|min|minutes?)\b` gives minutes × 60; otherwise the field is omitted and the caller falls back to the manifest's `rate_limit_recovery_seconds` (60). Hours, days and clock times are not parsed. `account/rateLimits/updated` and `codexErrorInfo` (`usageLimitExceeded`, `rateLimitExceeded`) are not read.

| Situation | Behaviour |
|---|---|
| Startup failure (`Session.start` raises anything) | Traceback logged; `error` `Codex owned execution could not start: <detail>`; `done {reason:"error"}`; cleanup in `finally` |
| Control process exits during the turn | `Session.events` raises `Codex control process exited before turn completion` (its exit waiter is raced against the next notification); the host backstop emits `error` + `done {reason:"error"}`; no `cycle_complete` |
| Transport failure (EOF, bad frame, oversized frame, reader cancelled, stdin write error, request timeout) | `ProtocolError`, same path. Texts include `Codex app-server disconnected before joined shutdown`, `Malformed Codex app-server JSON`, `Invalid Codex app-server frame size`, `Codex app-server frame exceeds its bound`, `Unexpected Codex app-server response`, `Codex app-server request bound reached` |
| Executor failure | `executor.check()` raises before and after each notification: `executor exited before owned retirement`, `executor control connection ended`, `executor connection is closed`, protocol refusals |
| Exit code / stderr | The exit code is never inspected: the control process is always stopped by cleanup, and a non-zero or signalled exit is not reported. stderr: last 64 KiB kept; after a non-cancelled turn it is logged as a warning (`codex stderr (turn=…)`) and never sent to the caller |
| Timeouts | 30 s per app-server request; 10 s `connectTimeoutMs`; 60 s for the launchd worker to connect; 15 s for coalition cleanup; 15 s per bridge I/O step. No overall turn timeout and no idle timeout: a silent turn waits until cancelled |
| Cleanup failure | `_cleanup_turn` raises; the process handle, session and image directory stay retained in the runner; the legacy store marks the turn `runner_failed` |

Cancel: `turn.cancel` calls `TurnRunner.cancel` (adds the id to `_cancelled`, cancels the running task) and then `TurnStore.cancel`. No `turn/interrupt` is sent; the turn ends because cleanup kills the app-server coalition. The runner's `finally` joins launch and cleanup even under repeated cancellation, then re-raises `CancelledError`; the host publishes `done {reason:"cancelled"}`. The runner's own `done {reason:"cancelled"}` branch is reached only if the loop sees the `_cancelled` flag without the task having been cancelled (inferred: not reachable through `TurnRunner.cancel`, which does both). Cancel before the app-server launch has returned is safe: `_launch_process` shields the launch and keeps the handle. Shell commands started through the exec-server are not signalled by cancel or by normal completion.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/rate_limit.py#RATE_LIMIT_INDICATORS`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/rate_limit.py#extract_recovery_seconds`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner.cancel`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner.run`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#AppServer._read`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#OwnedExecutor.check`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore._supervise_run`
- `arbol_deprecated_v1:tests/unit/test_native_domain_callers.py`

## 11. Recovery surface
Legacy host. State lives in `TurnStore`, in driver process memory only: per turn the detached task, the full ordered event list (appended only, never compacted), the live subscriber queues, `launch_receipt`, status, terminal flag, acknowledgement and `core_generation`. A driver restart loses all of it. The durable side files (native-domain journal, retirement marker, attempt-obligation records) hold ownership evidence, not events.

| Method | Returns | Semantics |
|---|---|---|
| `turn.inventory` | `turns[]`, `running` (turns with `work_pending`), `unacknowledged_terminal` | Every retained turn, running or finished |
| `turn.describe` | `found` and: `turn_id`, `launch_receipt`, `dispatcher_owner`, `status` (`running`, `completed`, `failed`, `cancelled`), `terminal`, `task_finished`, `runner_failed`, `authority_disposed`, `pending_mutations`, `mutation_failed`, `work_pending`, `earliest_seq`, `next_seq`, `last_seq`, `replay_available:true`, `subscriber_count`, `unresolved_waits` (always empty for this driver), `terminal_acknowledged`, `terminal_acknowledged_at`, `core_generation` | Read-only |
| `turn.attach` | describe row + `found`, `replay_available`, `requested_since_seq`, and `reason` when not available | Replay is available when the buffer is empty and `since_seq` is 0, or `since_seq >= earliest_seq - 1`. On success records `core_generation`. Unknown turn: `{found:false, replay_available:false, reason:"turn not found"}` |
| `turn.events` | events | Replays `seq > since_seq` verbatim (same `_ip_seq`), then live; duplicates suppressed; several subscribers may attach; a subscriber leaving does not affect the turn |
| `turn.ack` | `{found, acknowledged, terminal_seq}` or a `reason` | Accepted only when the last buffered event is `done` and `terminal_seq` equals `last_seq` (`turn is not terminal`, `terminal_seq N does not match last_seq M`). A later event clears the acknowledgement |

Retention: a turn is collected only by `gc_completed`, which runs at the start of each `turn.execute`: it must be terminal, acknowledged, cleanup-complete, and acknowledged more than `DEFAULT_COMPLETED_TTL_SECONDS` (300 s) ago. An unacknowledged terminal turn is kept indefinitely. After collection only the `turn_id` → receipt pair stays, so a re-execute is refused (`attempt replay was collected; launch cannot be repeated`). At most `MAX_LAUNCH_RECORDS` (100 000) records; collection is suspended while the store is sealed or a deployment fence is held. `done` maps to status: `cancelled` → `cancelled`, `error` → `failed`, anything else (including `rate_limited`) → `completed`.

State host. `StateProviderRuntime` keeps one record per attempt for the life of the process (records are never removed) and one `CheckpointStream` holding at most one unacknowledged checkpoint; the runner is back-pressured until `state.acknowledge` confirms the committed row. `DriverOutput` batches text into checkpoints of at most 32 KiB or 0.25 s, seals on `cycle_complete`/`done`, stores oversized tool settlements as content references, and maps `done` to phase `cancelled`, `failed` (any `error`/`rate_limited` seen, or reason `error`/`rate_limited`) or `completed`.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore.describe`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore.attach`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore.subscribe`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore.acknowledge_terminal`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#TurnStore.gc_completed`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#_status_for_done`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/execution.py#CheckpointStream`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/driver_output.py#DriverOutput`

## 12. Constants and limits
| Name | Value | Defined in | Purpose |
|---|---|---|---|
| `VERSION` / `DRIVER_NAME` / `PROVIDER` | `0.1.0` / `codex` / `codex` | `__init__.py` | Driver identity |
| `DEFAULT_MODEL` | `gpt-5.5` | `protocol.py` | Model when none is given |
| `_RESULT_TRUNCATE`; literals | `200 * 1024` characters; 1024 / 200 / 300 characters | `turn.py` | Tool result/error cap (legacy host only); `error.message` cap / `rate_limited.reason` cap / logged note cap |
| `MAX_FRAME` / `MAX_PENDING` / `STDERR_TAIL` / `REQUEST_SECONDS` | 8 MiB / 32 / 64 KiB / 30 s | `app_server.py` | Frame size / concurrent requests / kept stderr / per-request timeout |
| `MEMORY_BYTES`; literals | 1 MiB; `connectTimeoutMs` 10000, 128 MCP entries, `[A-Za-z0-9_-]{1,128}` | `notification_spool.py`; `session.py` | In-memory part of the notification backlog; executor attach timeout, MCP server count and name rule |
| `VERSION`; `EXECUTABLE_BYTES` / `EXECUTABLE_SHA256` | `0.159.2`; `240184096` / `16593cc2f422d5f398a8e40f550ebbaf1245392528957be342c295920a300704` | `executor.py` | Pinned Codex version and `codex` binary |
| `HOST_BYTES` / `HOST_SHA256` | `65359872` / `ed79fbc9e1683feb29d73fb421f3e16932d178a459f63741754014c6c7ea6107` | `executor.py` | Pinned `codex-code-mode-host` |
| `MAX_MESSAGE` / `MAX_PENDING` / `MAX_STREAM_BYTES` / `TAIL_BYTES` | 8 MiB / 32 / 256 MiB / 64 KiB | `executor.py` | Bridge message, pending requests, total exec-server output per turn, kept tail |
| `IO_SECONDS` / `DRAIN_SECONDS`; literals | 15 / 1; 1 s + 1 s | `executor.py`; `tool_process.py` | Bridge write timeout / close timeouts; wait before `terminate`, then before `kill` |
| `WORKER_START_SECONDS` / `HANDSHAKE_SECONDS` / `CLEANUP_SECONDS` / `MAX_DOMAINS` | 60 / 12 / 15 / 4096 | `native_domain.py` | Worker connect, handshake, coalition cleanup, journal capacity |
| `DEFAULT_COMPLETED_TTL_SECONDS` / `MAX_LAUNCH_RECORDS`; `TURN_PROTOCOL_VERSION` / `LAUNCH_PROTOCOL` | 300.0 / 100 000; 2 / 1 | `turn_store.py`; `provider_protocol.py` / `provider_launch.py` | Post-acknowledge retention / launch records; recovery protocol / launch protocol |
| `BUFFER_BYTES`; `rate_limit_recovery_seconds` | 32 KiB; 60 | `state/driver_output.py`; `manifest.json` | Checkpoint text size (state host); caller's default rate-limit cool-down |
| `EXECUTE_TIMEOUT_SECONDS` / `DESCRIBE_TIMEOUT_SECONDS` / `EXECUTE_COORDINATION_ATTEMPTS` | 20 / 10 / 3 | `chat_session_orchestrator.py` (caller) | Caller's `turn.execute` budget |

| Environment variable | Default | Read in | Effect |
|---|---|---|---|
| `CODEX_BIN` | `codex` | `__main__.py`, `state_main.py`, `server.py` | Name or path of the CLI |
| `ARBOL_DRIVER_CODEX_SOCKET_NAME`; `ARBOL_APP_SUPPORT` | `driver.codex`; `~/Library/Application Support/Arbol` | both entry points; `paths.py` | Socket file stem; root of `run/`, `logs/` |
| `ARBOL_STATE_RUNTIME_FILE`, `ARBOL_STATE_BINDING_SHA256` | unset | `state/bootstrap.py` | Selects and pins the state binding |
| `ARBOL_PROVIDER_BUILD_ID`, `ARBOL_PROVIDER_INSTANCE_ID`, `ARBOL_PROVIDER_DRIVER_ID`, `ARBOL_PROVIDER_GENERATION` | `dev`, `codex@<build>`, `arbol_driver_codex`, `provider-r1` | `provider_protocol.py` | Health/launch identity |
| `ARBOL_IMPORT_SELFTEST`; `ARBOL_KN_CODE_ROOT` | unset; `~/repo/sylvan-stack/Arbol` | `selftest.py`; `system_prompt.py` | `1` = import check, then exit; adds the code-navigation section |
| `ARBOL_ARTIFACTS_ROOT`, `ARBOL_SYSTEM_INSTRUCTIONS_REPO`, `ARBOL_REPO_ROOT` | `~/Artifacts`, `Arbol`, `~/repos` | `system_instructions.py` | Where templates and chapters are read |
| `PATH`, `HOME`, `CODEX_HOME`; `CODEX_EXEC_SERVER_URL` | inherited; set to `none` for the app-server | `turn.py`, `session.py` | Sections 4 and 5; stops Codex from choosing its own executor (inferred purpose) |
| `CODEX_EXEC_SERVER_NOISE_*` (four); `ARBOL_LIFECYCLE_APPROVAL_SOCKET` | must be empty; removed from the child environment | `session.py`; `turn.py` | Refusal 1 of section 5; left over from the removed approval bridge |
| `ARBOL_CODEX_SANDBOX`, `ARBOL_CODEX_NETWORK` | unset | `protocol.py` | Read only by dead functions; no effect on a turn |

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#_RESULT_TRUNCATE`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#sandbox_mode`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/native_domain.py`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#DEFAULT_COMPLETED_TTL_SECONDS`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_protocol.py#instance_identity`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/system_instructions.py#shared_chapter_path`
- `arbol_deprecated_v1:daemons/core/arbol_core/chat_session_orchestrator.py`

## 13. Tests as evidence
| Test file | Behaviours it pins |
|---|---|
| `tests/unit/test_codex_app_server.py` | Request/response correlation out of order and across fragmented frames; an error reply rejects one request only; malformed, oversized, uncorrelated or non-finite frames fail every waiter; 32-request and 8 MiB bounds; a notification burst does not block replies; the request timeout covers a blocked write; stderr tail is bounded; `close()` joins both readers; server requests are never granted; item, usage, error and terminal mapping |
| `tests/unit/test_codex_session.py` | Exact argv, `CODEX_EXEC_SERVER_URL=none`, exact request order; `thread/start` and `turn/start` payloads; every refusal of section 5 happens before the thread or executor exists; the saved config object is not mutated; a failed start keeps both handles until cleanup; cancellation during either launch is joined; control exit is detected without waiting for stdout EOF; `tool_policy` is always full access with network |
| `tests/unit/test_codex_cli_turn.py` | Event order per scenario; `usage` carries the requested model; rate-limit, login and model-version classification and texts; startup failure text; param validation texts; prompt content; `PATH` overlay; cancel joins both processes and re-raises; `full_permissions` and the two obsolete env variables change nothing; image files reach `turn/start` and are deleted afterwards; `tool_use_id` differs between two runs of one turn |
| `tests/unit/test_codex_cli_protocol.py` | Thinking → effort map; prompt rendering; `map_exec_event` on exec-style records; plus the dead `build_argv` / `sandbox_mode` / `network_access_enabled` helpers |
| `tests/unit/test_codex_executor.py` | Executor argv and typed policy; binary and code-mode-host pinning (size, hash, mode, owner, layout, symlink and race cases); bridge refusals (origin, secret, second attachment, sandbox/proxy fields, replayed `initialize`, duplicate JSON keys, pending limit, version drift); output overflow retires the executor; cleanup failures keep the handle |
| `tests/unit/test_codex_tool_process.py` | A detached server started by a tool survives executor cleanup; the retirement receipt must match the reaped child |
| `tests/unit/test_codex_ip_scaffold.py` | `ping`, `healthz` fields, `missing turn_id`, idempotent `turn.execute` with equal `launch_receipt`, `unknown method`, stream errors, `_ip_seq` on every event; shipped manifest values; registry scan and the seeded `codex` → `codex-chatgpt` Subscription binding |
| `tests/unit/test_codex_permission_options.py` | The caller forwards `full_permissions` and `model` from route settings; no settings → empty options |
| `tests/unit/test_native_codex_policy.py` | `CodexToolPolicy` and `captured_tmpdir` input validation |
| `tests/unit/test_native_domain_callers.py` | The runner launches only through `native_domain`, never `killpg` or a plain subprocess; an unresolved launch or failed cleanup keeps handles and image directory; normal, cancel and error ends all run the joined cleanup |
| `tests/unit/test_native_build_capability.py` | The import self-test loads `state.provider_entrypoint`, `arbol_driver_codex.server` and `arbol_driver_codex.session` |
| `tests/unit/test_native_codex_probe.py` | Unit tests of `tests/fixtures/native_codex_probe.py`, a plan-only harness for manual probes of a real control/executor pair; they cover the harness, not the driver |
| `tests/state/test_codex_state_execution.py` | Real runner, bridge and exec-server against a scripted control peer (`tests/fixtures/state_codex_control.py`) under the state host: text, reasoning, a 266 kB tool result stored complete, attempt released |
| `tests/state/test_intake_policy.py` | `native_cli` binding: options returned without reading any stored credential |
| `tests/smoke/test_ip_codex_ping.py`; `tests/fixtures/mock_codex.py` | The daemon boots from source or binary and answers `ping` / `healthz`. The fixture is a leftover fake of `codex exec --json`; no test runs it |

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:tests/unit/test_codex_app_server.py`
- `arbol_deprecated_v1:tests/unit/test_codex_session.py`
- `arbol_deprecated_v1:tests/unit/test_codex_cli_turn.py`
- `arbol_deprecated_v1:tests/unit/test_codex_cli_protocol.py`
- `arbol_deprecated_v1:tests/unit/test_codex_executor.py`
- `arbol_deprecated_v1:tests/unit/test_codex_tool_process.py`
- `arbol_deprecated_v1:tests/unit/test_codex_ip_scaffold.py`
- `arbol_deprecated_v1:tests/unit/test_codex_permission_options.py`
- `arbol_deprecated_v1:tests/unit/test_native_codex_policy.py`
- `arbol_deprecated_v1:tests/unit/test_native_domain_callers.py`
- `arbol_deprecated_v1:tests/unit/test_native_build_capability.py`
- `arbol_deprecated_v1:tests/unit/test_native_codex_probe.py`
- `arbol_deprecated_v1:tests/state/test_codex_state_execution.py`
- `arbol_deprecated_v1:tests/state/test_intake_policy.py`
- `arbol_deprecated_v1:tests/smoke/test_ip_codex_ping.py`
- `arbol_deprecated_v1:tests/fixtures/mock_codex.py`

## 14. Defects, dead code and oddities
| # | Finding | Ref |
|---|---|---|
| 1 | `protocol.py` still documents and implements the retired `codex exec --json` route: `build_argv`, `sandbox_mode`, `network_access_enabled`, `DEFAULT_SANDBOX`, `_SANDBOX_MODES` are called only by tests. Live output goes through an adapter that first rewrites app-server items into the old record shape | `protocol.py#build_argv`, `app_server.py#exec_events` |
| 2 | `fileChange.changes` is an array of `{path, kind, diff}` in the app-server protocol, but the summary code expects a path-keyed object; for arrays the settled `result`/`error` is Python's `str()` of the list, diffs included | `protocol.py#_item_events` |
| 3 | `full_permissions`, `fast_mode`, `oauth_token`, `account_id`, `provider_base_url` are accepted and silently ignored. Fast mode is offered for this route and does nothing | `turn.py#TurnRunner._run_one_cycle` |
| 4 | `healthz` advertises `feed_permission_recovery`, while `feed_permission` always returns `False` | `server.py#handle`, `turn.py#TurnRunner.feed_permission` |
| 5 | `codex_version` is always `unknown` and `_cli_version()` always `None`, so the model-version hint always says `version unknown`; the "pin the observed CLI version" log line logs `unknown` | `server.py#_codex_version`, `turn.py#_cli_version` |
| 6 | Classification by substring: `429`, `401`, `quota`, `unauthorized` match anywhere in a message (ids, paths, quoted output). Rate limit is tested first, so a login failure text containing `quota` or `429` becomes a rate limit. Structured `codexErrorInfo` is ignored | `rate_limit.py#is_rate_limit_text` |
| 7 | Retry hints understand only seconds and minutes after three fixed phrases | `rate_limit.py#extract_recovery_seconds` |
| 8 | No overall or idle timeout for a turn; a stalled Codex turn holds two processes until cancelled | `session.py#Session.events` |
| 9 | Cancel never sends `turn/interrupt`; it kills the app-server. Commands started through the exec-server survive cancel and completion by design | `turn.py#TurnRunner.cancel`, `tool_process.py#ToolProcess._cleanup` |
| 10 | The runner's `done {reason:"cancelled"}` branch and its `_cancelled` loop check are effectively dead; the host supplies the terminal (inferred) | `turn.py#TurnRunner._run_one_cycle` |
| 11 | Raised failures (control exit, protocol error, interrupted turn) skip `cycle_complete`, while fatal messages emit it: two shapes for a failed turn | `turn.py#TurnRunner._run_one_cycle`, `turn_store.py#TurnStore._supervise_run` |
| 12 | The driver is hard-pinned to one binary by size and SHA-256; any CLI update makes every turn fail at startup until the driver is rebuilt | `executor.py#verify_executable` |
| 13 | A harmless `<home>/.env` or `environments.toml`, or any `model_providers` entry, blocks every turn; the Leather Bag sees only the refusal text | `session.py#Session.start` |
| 14 | Managed requirements other than `network`, `hooks`, `defaultPermissions`, `featureRequirements` are not checked; the driver always asks for `never` + full access regardless of `allowedApprovalPolicies` / `allowedSandboxModes` | `session.py#validate_config` |
| 15 | Only `workspace_dirs[0]` reaches Codex as cwd/root; further directories appear only in the prompt | `session.py#Session.start` |
| 16 | Unused parameters and code: `Session.start` takes `sandbox` and `network`; `tool_policy` takes `config`, `sandbox`, `network`, `env`; `_env_overrides_for` takes `options`; `TurnRunner.stash` / `_pending` have no caller; the `TMPDIR` check in `start_executor` is unreachable for the only policy mode used | `session.py#tool_policy`, `turn.py#TurnRunner.stash`, `executor.py#start_executor` |
| 17 | Stale comments: `server.py` says cancel does "SIGTERM→SIGKILL the subprocess's process group" and that the runner owns "JSONL mapping"; `_env_overrides_for` says the launchd `PATH` lacks `~/bin` and Homebrew, while both plist templates include them; version notes disagree (`executor.py` `0.159.2`, probe fixture `0.155`, `protocol.py` `0.147.0`) | `server.py#handle`, `turn.py#_env_overrides_for` |
| 18 | The system prompt is concatenated into the first user input instead of `baseInstructions` / `developerInstructions`; the whole earlier conversation and all earlier images are re-sent every turn in one text block, with tool calls and reasoning of earlier turns dropped | `protocol.py#render_prompt`, `images.py#prepare_images` |
| 19 | `usage` reports the requested model even if Codex rerouted, and drops cached/reasoning token counts | `protocol.py#usage_from` |
| 20 | The notification backlog can grow without bound on disk | `notification_spool.py#NotificationSpool` |
| 21 | In legacy mode the driver needs a Postgres connection at start just to learn it is in legacy mode | `state/bootstrap.py#configured_binding` |
| 22 | Unknown-turn replies of the raw handler (`found:false`, stream `missing turn_id`) are masked by the authentication wrapper's single refusal text | `provider_authority.py#authenticated_handler` |
| 23 | `rate_limited` turns get store status `completed` | `turn_store.py#_status_for_done` |
| 24 | The agent-facing template tells Codex that the CLI configuration and Full Permissions govern its sandbox and that lifecycle actions need approval; none is true for this driver (corpus file `system-instructions/codex-native.md.tmpl`) | `system_prompt.py#render_codex_system_prompt` |

Documentation check: `product-spec/03-turn-execution.md`, `05-intelligence-providers.md` and `06-tools-and-permissions.md` match the code on every Codex-route point compared (fresh thread per attempt with a transcript prompt, no credential injection, the refusal list, the effort table, no effect of fast mode and Full Permissions), except the approval nuance in section 8 and that the effort table omits the accepted input `low`. `architecture/native-tools.md` matches on the `tool_use_id` prefix. `architecture/codex-inference-plan.md` describes the direct-backend `universe` route, not this driver.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#build_argv`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#_item_events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/server.py#_codex_version`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#_cli_version`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/turn.py#TurnRunner.stash`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/rate_limit.py#is_rate_limit_text`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#validate_config`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#tool_policy`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#verify_executable`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/notification_spool.py#NotificationSpool`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/provider_authority.py#authenticated_handler`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/turn_store.py#_status_for_done`
- `arbol_deprecated_v1:daemons/shared/arbol_shared/state/bootstrap.py#configured_binding`

## 15. Installed CLI comparison
Installed: `codex-cli 0.159.2`, a Homebrew cask at `/opt/homebrew/Caskroom/codex/0.159.2/bin/codex`. Its size and SHA-256, and those of the sibling `codex-code-mode-host`, equal v1's four pinned constants; `../codex-resources/` holds only `voice` and `zsh`. So v1 is pinned to exactly the installed build (whether its layout checks pass was not run).

### 15.1 Flags, config overrides and environment
| v1 uses | In 0.159.2 help | Note |
|---|---|---|
| `codex app-server --listen stdio://` | yes; the subcommand is marked `[experimental]`; `stdio://` is the default (`--stdio` is an alias; also `unix://`, `ws://IP:PORT`, `off`) | Also has `daemon`, `proxy`, `generate-ts`, `generate-json-schema` |
| `-c key=value`, `-c features.<name>=false\|true` | yes (TOML value, raw string on parse failure); `--disable <FEATURE>` / `--enable <FEATURE>` are equivalent | All 29 names appear in `codex features list` |
| `-c notify=[]` | `-c` exists; the key itself is not in help | Not established from help |
| `codex exec-server --listen stdio` | yes, marked `[EXPERIMENTAL]`; `stdio` and `stdio://` accepted | Has `--exit-on-stdin-close`, which v1 does not pass |
| env `CODEX_EXEC_SERVER_URL=none`, `CODEX_EXEC_SERVER_NOISE_*` | not in help | Names occur in the binary's strings; effect not established |
| env `CODEX_HOME` | mentioned in help (`--profile`, `--ignore-user-config`) | |
| Hints `codex login`, `codex update` | both exist | `login` has `status`, `--with-api-key`, `--with-access-token`, `--device-auth` |
| Dead `build_argv`: `exec`, `--json`, `--ephemeral`, `--skip-git-repo-check`, `--sandbox`, `-C`, `--add-dir`, `-m`, `--image`, `-c model_reasoning_effort=`, `-c sandbox_workspace_write.network_access=`, `-c approval_policy=never` | every flag exists in `codex exec --help`; the three config keys are not in help | Unused by v1 at run time |

Nothing v1 passes has disappeared from help. Options in 0.159.2 that v1 does not use and a rewrite may want: `--strict-config`, `--code-mode-host <URL>`, `app-server daemon` / `proxy`, the `--ws-*` authentication options, `--dangerously-bypass-approvals-and-sandbox`, and (shown for `exec`, not for `app-server`) `-p/--profile` and `--ignore-user-config`.

### 15.2 Protocol names against the generated schema
Schema generated twice: default into `…/scratchpad/codex-schema` and with `--experimental` into `…/scratchpad/codex-schema-experimental` (the output option is `-o, --out <DIR>`). "Stable" means present without `--experimental`.

| v1 name | Kind | Stable | Experimental | Note |
|---|---|---|---|---|
| `initialize`, `initialized` | client request, client notification | yes | yes | `capabilities.experimentalApi` exists |
| `config/read` | client request | yes | yes | `cwd`, `includeLayers` exist; the result `Config` types `model_provider` and allows additional properties; the other keys v1 checks are not typed |
| `configRequirements/read` | client request | yes | yes | `defaultPermissions`, `featureRequirements` are stable; `network`, `hooks` are experimental-only |
| `thread/start` | client request | yes | yes | `environments` is experimental-only; `sandbox` has `danger-full-access`; `approvalPolicy` has `never`; `serviceTier`, `baseInstructions` exist |
| `environment/add`, `environment/info`, `environment/status` | client requests | **no** | yes | `environmentId`, `execServerUrl`, `connectTimeoutMs`, plus `authBearerToken`; status kinds `ready`, `pending`, `disconnected`, `unknown` |
| `turn/start` | client request | yes | yes | `environments` is experimental-only; `sandboxPolicy` has `externalSandbox` with `networkAccess` `restricted`/`enabled`; input kinds `text`, `localImage` exist; `effort` is a free non-empty string; `serviceTier`, `summary` exist |
| `item/commandExecution/requestApproval`, `item/fileChange/requestApproval` | server requests | yes | yes | command decisions `accept`, `acceptForSession`, `acceptWithExecpolicyAmendment`, `applyNetworkPolicyAmendment`, `decline`, `cancel`; file-change decisions `accept`, `acceptForSession`, `decline`, `cancel` |
| `item/permissions/requestApproval` | server request | yes | yes | response `permissions` (required), `scope` (`turn`, `session`), `strictAutoReview` |
| `item/started`, `item/completed` | notifications | yes | yes | item types used by v1 exist: `agentMessage`, `reasoning`, `commandExecution`, `fileChange`; statuses `inProgress`, `completed`, `failed`, `declined` |
| `thread/tokenUsage/updated` | notification | yes | yes | `tokenUsage.last` / `total` with `inputTokens`, `cachedInputTokens`, `outputTokens`, `reasoningOutputTokens`, `totalTokens` |
| `error`, `turn/completed` | notifications | yes | yes | `willRetry`, `error.message`, `error.codexErrorInfo`; `turn.status` ∈ `completed`, `interrupted`, `failed`, `inProgress` |

The exec-server protocol the bridge validates (`process/*`, `fs/open`, `fs/readBlock`, `fs/walk`, `fs/canonicalize`, `process/output`, `process/closed`, …) is not covered by this schema generator and was not compared.

Current names a rewrite needs for Subscriptions and approvals (names only):
- Account requests: `account/read`, `account/login/start`, `account/login/cancel`, `account/logout`, `account/usage/read`, `account/workspaceMessages/read`, `account/sendAddCreditsNudgeEmail`, `account/gatewayOAuth/login`, `account/gatewayOAuth/read`, `account/gatewayOAuth/cancel`; experimental `account/bedrock/discover`, `account/bedrock/setup`. Account notifications: `account/updated`, `account/login/completed`, `account/gatewayOAuth/changed`, `modelProvider/authRecoveryStarted`, `modelProvider/authRecoveryCompleted`. Server request: `account/chatgptAuthTokens/refresh`.
- Login variants of `account/login/start`: `apiKey`, `chatgpt`, `chatgptDeviceCode`, `chatgptAuthTokens`, `amazonBedrock`, `amazonBedrockAccessKeys`. Account kinds in `account/read`: `apiKey`, `chatgpt`, `amazonBedrock`.
- Rate limits: requests `account/rateLimits/read`, `account/rateLimitResetCredit/consume`; notification `account/rateLimits/updated`. Models: requests `model/list`, `modelProvider/capabilities/read`; notifications `model/rerouted`, `model/verification`, `model/safetyBuffering/updated`.
- Approval-related server requests: `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput`, `item/tool/call`, `mcpServer/elicitation/request`, `applyPatchApproval`, `execCommandApproval`, `attestation/generate`. Other approval-related names: notifications `serverRequest/resolved`, `item/autoApprovalReview/started`, `item/autoApprovalReview/completed`, `autoApprovalReview/strictReviewRequired`, `guardianWarning`; client requests `thread/approveGuardianDeniedAction`, `permissionProfile/list`.
- Turn control and streaming v1 never used: `turn/interrupt` (`threadId`, `turnId`), `turn/steer`, `thread/resume`, `thread/fork`, `thread/read`; notifications `item/agentMessage/delta`, `item/reasoning/summaryTextDelta`, `item/reasoning/textDelta`, `item/commandExecution/outputDelta`, `turn/started`, `turn/plan/updated`, `turn/diff/updated`.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#control_argv`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#AppServer._dispatch`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/app_server.py#exec_events`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#start_executor`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#EXECUTABLE_SHA256`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/protocol.py#build_argv`

## 16. Not established
- Whether v1 ever ran a real turn against 0.159.2 on this machine, and whether its layout checks pass for the Homebrew cask install. Nothing was executed.
- What Codex does with `CODEX_EXEC_SERVER_URL=none`, with `notify=[]`, and with each feature flag; only that the names exist in the installed build.
- Whether `config/read` really returns the keys v1 checks (`model_providers`, `permissions`, `default_permissions`, `network`, `features`, `notify`, `mcp_servers`); the schema types only `model_provider`.
- Whether Codex honours `effort` values `low`…`xhigh` for every model, and which models the logged-in account may use; `model/list` was not called.
- Whether `thread/tokenUsage/updated` arrives once per model request or once per turn, and therefore whether the caller's summing of `usage` events over-counts.
- The real shape of `error.message` for usage limits and login failures in 0.159.2; the classification patterns were read, not observed.
- What the exec-server does to running commands when its stdin closes or it is terminated (v1 assumes they survive, and a test pins that for a detached server only), and the exec-server protocol's current method names (the schema generator covers the app-server only).
- Which launchd environment the installed v1 driver actually had (templates were read, no installed plist was inspected), hence whether API-key variables reached Codex. Likewise the content of the live templates under `~/Artifacts/Arbol/system-instructions/`; only the copy in the deprecated documentation corpus was read.
- Root-side Subscription behaviour (login import, usage meters, model catalogue) beyond the two touch points named in section 9; out of scope here.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#Session.start`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/executor.py#resolve_executable`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/tool_process.py#ToolProcess._cleanup`
