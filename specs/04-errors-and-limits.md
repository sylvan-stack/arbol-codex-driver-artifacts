---
role: authored
spec: CDX-4
status: accepted
---
# Codex Driver · 04 Errors and limits

How the Codex Driver meets [DRV-4](../../arbol/driver-contract/04-errors-and-limits.md): which fields of the `codex` tool's protocol decide the error code of a failed run, how the three places a failure can appear are told apart, what the tool reports about the account's limits, and the time limits. It matters because the tool states a class for every failure in a field of its own, which version 1 did not read, and because several failures a caller cares about, such as an unknown model, arrive in that field only as "other" with the vendor's answer as text.

Everything stated about the installed tool was observed on 5 October 2026 with `codex-cli` 0.159.2 and is recorded in the [probe record](../research/tool-probes-2026-10-05.md).

## Scope

Covered: the mapping from the tool's error information to error codes, the tool's own retries, limit information, time limits, the tool's version.

Not covered: the contract (DRV-4); the events of a run (CDX-2); tools (CDX-3).

## Behaviour

### Where a failure appears

| Place | What it means | What the Driver does |
|---|---|---|
| An error answer to one of the Driver's requests | The request was not carried out | Before the turn: the run is refused or fails as stated in CDX-2. A refused `thread/resume` leads to a rebuild |
| An `error` notification with `willRetry` true | The tool is retrying | A `notice` |
| An `error` notification with `willRetry` false, followed by `turn/completed` with status `failed` | The turn has failed | `finished` as `failed`, with the code from the table below |
| The process ends before `turn/completed` | The tool failed | `finished` as `failed` with `tool_failed` and the end of the tool's log |

A declined or refused tool call is not a failure of the run: the turn completes and the call is reported as failed.

### From the tool's error information to an error code

The final `error` notification and the failed turn carry the same object: a message, an optional detail, and `codexErrorInfo`, the tool's own class of the failure. The code is decided by the first row that matches:

| `codexErrorInfo` | Code |
|---|---|
| `unauthorized`, or any class that carries a status of 401 or 403 | `credential_rejected` |
| `usageLimitExceeded`, `rateLimitExceeded` | `rate_limited` |
| `contextWindowExceeded` | `context_exceeded` |
| `serverOverloaded`, `internalServerError`, `flexUnavailable`, or a connection class with a status of 500 or above or with no status | `vendor_unavailable` |
| `cyberPolicy`, `misalignmentPolicyViolation`, `tooManyDenials`, `badRequest`, `sessionBudgetExceeded` | `vendor_error` |
| `sandboxError`, `threadRollbackFailed`, `activeTurnNotSteerable` | `tool_failed` |
| `other`, and the message is the vendor's answer with status 400 naming a model that is not supported, or an unsupported value for the effort | `invalid_input` |
| `other`, and the message says the model requires a newer version of the tool | `tool_unsupported` |
| `other` or none, and the message matches the wording lists | `rate_limited` or `credential_rejected`, with the detail saying it was decided by wording |
| Anything else | `vendor_error` |

The connection classes are those that carry a status of their own: a failed connection, a failed or broken response stream, and too many failed attempts.

Observed with the installed tool: only three classes occurred. A turn in a home without a login was retried with the class of a broken response stream and status 401, and failed with the class of a failed connection and status 401; the class `unauthorized` was not used. An unknown model and an effort the model does not take both failed with the class `other` and the vendor's answer, a JSON text with status 400, as the message. An effort the model does not list was once accepted without any error.

Observed on 6 October 2026, with the vendor made unreachable through a proxy address where nothing listens: `account/read`, `model/list` and `thread/start` answered as usual. The turn brought `error` notifications with `willRetry` true and the class of a broken response stream without a status: "Reconnecting... 2/5" to "5/5" within 3 seconds, a `warning` that the tool was falling back from WebSockets to HTTPS, and then "Reconnecting... waiting for network" again and again, 8 to 43 seconds apart. The turn had not ended 150 seconds after its start.

Observed in version 1: the class was not read. The message was searched for fragments, rate limits first, then a too-new model, then login failures.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/rate_limit.py#is_rate_limit_text
arbol:drivers/codex/arbol_driver_codex/turn.py#TurnRunner._run_one_cycle
arbol:drivers/codex/arbol_driver_codex/protocol.py#map_exec_event
-->

### The wording lists

Used only by the last-but-one row above. They are version 1's, without the bare fragments `429`, `401`, `quota` and `unauthorized`, which match identifiers and quoted output.

| Class | Phrases, matched without regard to case |
|---|---|
| Rate limit | `rate limit`, `rate_limit`, `too many requests`, `usage limit`, `usage cap`, `insufficient_quota`, `limit reached`, `you've hit your`, `you have hit your`, `weekly limit`, `daily limit` |
| Rejected credential | `not logged in`, `logged out`, `codex login`, `invalid api key`, `missing credentials`, `please login` |
| Tool too old | `requires a newer version of codex`, `requires a newer version of the codex` |

A wait is read from the text as in CLD-4: "retry in", "try again in" or "wait", a number, and its unit.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/rate_limit.py#extract_recovery_seconds
arbol:drivers/codex/arbol_driver_codex/rate_limit.py#AUTH_ERROR_INDICATORS
-->

### The tool's own retries

The tool reconnects by itself and announces each attempt with an `error` notification whose `willRetry` is true. The Driver emits a `notice` for each. When such a notification carries status 401 or 403, the Driver stops the run at once and finishes it as `failed` with `credential_rejected`.

Because the Driver checks the account before every turn (CDX-2.3), this is the path for a login that fails during a run, not for one that is missing.

Observed with the installed tool: without a login, four retries over a streaming connection, a change to another connection type with a warning, five more retries, and the final failure after about 15 seconds.

### Limit information

The tool sends `account/rateLimits/updated` after every request to the model. The Driver keeps the latest and turns it into the Subscription's usage report when the run ends, by the mapping of CDX-1. The notification is sparser than the answer to a request: it lacks the reason a limit was reached. Where the stored report already holds a value the notification lacks, the stored value is kept.

When a run fails with `rate_limited`, the Driver sends one `account/rateLimits/read` before it ends the process and takes the wait from the reset time of the window that is used to 100 percent. The request is the tool's own and costs nothing.

Observed with the installed tool: with the weekly window at 100 percent and credits on the account, runs continued and were charged to the credits. No limit error occurred, so the shape of one is not known.

### Time limits

| Limit | What counts for this tool |
|---|---|
| Start | The answer to `turn/start`, within the 60 seconds of DRV-4. Inside that time each request before it has 30 seconds of its own (CDX-2.6) |
| Idle | Any notification is a sign of life, including the tool's retries |
| Shell commands | The tool's own setting; the Driver does not change it |

While the vendor cannot be reached the tool goes on retrying, and every retry is a sign of life. The idle limit therefore does not end such a run: it waits, with one `notice` per retry, until the network is back, the run is stopped or its total limit is reached.

A tool call that is running stops the idle clock (DRV-4.10). For this tool a tool call is running from its item's start to its completion, which covers a command the agent left running when its turn completed.

### The tool's version

The Driver reads the version from the answer to the handshake of every process. A version below the oldest supported one, 0.159.2, fails the run with `tool_unsupported`, naming both versions. So does a home whose configuration the tool reports as invalid or does not apply (CDX-2.2), since that means the Driver's configuration does not fit this version of the tool.

Observed in version 1: the version was never read, and the hint for a model that needs a newer tool always said "version unknown". One exact build was accepted, by checksum.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/turn.py#_cli_version
arbol:drivers/codex/arbol_driver_codex/executor.py#verify_executable
-->

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-4.1 | decide the error code of a failed turn from `codexErrorInfo` by the mapping table, first matching row | DRV-4.4 | Changed | Pending SYL-91 for the complete structured mapping; `C12` and `Mapper.test_protocol_malformed_foreign_notices_outcome_and_utf8_truncation` preserve the implemented generic `vendor_error` path only |
| CDX-4.2 | read the vendor's answer in the message of an error of class `other` to recognise an unsupported model and an unsupported effort | DRV-4.4 | New | Pending SYL-91 for parsing vendor class `other`; `C40` (fresh-run scope) checks preflight model/effort refusals only; dated real vendor answers are historical observations |
| CDX-4.3 | use the wording lists only for the class `other` or a missing class, and mark the error as decided by wording | DRV-4.4 | Changed | Pending SYL-91 for run-error wording precedence and classification detail; `AppServerTests.test_authentication_rejection_is_specific_and_diagnostics_are_bounded` covers account RPC rejection only |
| CDX-4.4 | emit a `notice` for every `error` notification whose `willRetry` is true | DRV-4.12 | New | The baseline retry-notice mapper is retained; complete retry/error conformance remains pending SYL-91 and is not part of the retained scoped suites |
| CDX-4.5 | stop the run at the first retry notification with status 401 or 403 and finish it as `credential_rejected` | DRV-4.8 | New | Pending SYL-91 (first rejected retry, turn interruption and account attention state); historical no-login vendor retries do not establish current Python handling |
| CDX-4.6 | keep the latest `account/rateLimits/updated` of a run and store it as the Subscription's usage report when the run ends, without losing values the notification lacks | DRV-4.13 | New | Pending SYL-91 for run-derived limits and sparse-update preservation; `C41`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` and `Accounts.test_usage_last_good_cache_rejection_and_catalog_fallback` cover subscription-command usage only |
| CDX-4.7 | on a `rate_limited` failure, ask the tool once for the account's limits before ending the process and take the wait from the exhausted window | DRV-4.5 | New | Pending SYL-91 (one post-limit read and exhausted-window wait); real reached-limit behavior remains unobserved |
| CDX-4.8 | treat every notification as a sign of life | DRV-4.9 | New | Pending SYL-91 for idle-clock enforcement and notification heartbeats; `AppServerTests.test_timeout_and_cancellation_include_blocked_stdin_drain` covers RPC timeouts only |
| CDX-4.9 | report a process that ends before `turn/completed` as `tool_failed`, with at most 1 KiB from the end of its log | DRV-4.2 | Changed | `C42`; `AppServerTests.test_malformed_oversized_boolean_id_exit_and_internal_request_timeout`; `AppServerTests.test_authentication_rejection_is_specific_and_diagnostics_are_bounded` (unexpected transport end and final diagnostic capped at 1 KiB) |
| CDX-4.10 | read the tool's version from the handshake and fail the run on a version below the oldest supported one | DRV-4.14 | Changed | `C31` (missing/old tool preflight) and migration no-prompt version probe; enforcement of an unsupported handshake version remains pending SYL-91 |

## Python migration verification on 7 October 2026

SYL-95 preserves the implemented generic failed-turn result, typed account RPC rejection, request timeouts, bounded transport diagnostics and vendor-version preflight in Python. It does not implement the complete error mapping, retry interruption, run-derived limit reports or run clocks specified here. The table distinguishes those partial checks from pending SYL-91; the shared error/limit scenarios `C26`–`C30` are not included in the retained wrappers. Advanced tools remain pending SYL-90, complete development/live checks remain pending SYL-92, and the first working numbered Codex Build remains pending SYL-94.

Current names of the form `Class.method` refer to unittest methods under `tests/`, run on pinned CPython 3.14.8 from source, the standalone development candidate and its relocated copy. Evidence: `research/python-migration-2026-10-07/verification.json`, `research/python-migration-2026-10-07/packaged-unit.txt`, `research/python-migration-2026-10-07/scoped-conformance-base.txt`, `research/python-migration-2026-10-07/scoped-conformance-runs.txt`, `research/python-migration-2026-10-07/no-prompt-probes.json` and `research/python-migration-2026-10-07/standalone-rehearsal.json`. The real migration probes sent no prompts. Dated vendor failure and retry observations in this document remain historical schema/probe evidence and do not establish fresh Python live handling; unobserved vendor failures below remain unobserved.

## Not established

- The class and message of a reached usage limit, a rate limit, an expired login and an overloaded vendor. None occurred. The rows for them follow the tool's schema, not an observation.
- Whether the tool ever gives up while the vendor cannot be reached. It was still retrying after 150 seconds.
- When the detail beside the message is filled on a final error.
- What `sessionBudgetExceeded` means; it is mapped to `vendor_error` until seen.

## Known problems in version 1

Not to be reproduced.

- **A fragment anywhere in the message decided the class**, rate limit first, so a login failure that mentioned a quota was reported as a limit.
- **A missing login cost fifteen seconds** and ended with a hint in the text, without any change of state.
- **The tool's limit notifications were ignored.**
- **One build of the tool was accepted**, and its version was never read.

<!-- sources:
arbol:drivers/codex/arbol_driver_codex/rate_limit.py#is_rate_limit_text
arbol:drivers/codex/arbol_driver_codex/executor.py#verify_executable
-->

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D11 | Is the vendor's answer inside the message of class `other` parsed? | Yes, for the two cases a caller can act on: an unsupported model and an unsupported effort. Everything else of that class is `vendor_error` with the text as the message | Decided 6 October 2026 by the owner: yes (SYL-68) |
| CDX-D12 | Is the account's limit read once more after a limit failure? | Yes: it is the only way to tell the caller how long to wait | Decided 6 October 2026 by the owner: yes (SYL-69) |
