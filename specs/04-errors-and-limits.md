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
| CDX-4.1 | decide the error code of a failed turn from `codexErrorInfo` by the mapping table, first matching row | DRV-4.4 | Changed | `C26`; `RunErrors.test_every_structured_class_and_exact_retry_policy`, `RunErrors.test_connection_statuses_and_first_row_precedence`, `RunErrorEvents.test_final_error_notification_and_turn_failure_both_use_classifier` |
| CDX-4.2 | read the vendor's answer in the message of an error of class `other` to recognise an unsupported model and an unsupported effort | DRV-4.4 | New | `C26`; `RunErrors.test_other_vendor_json_model_and_effort_refusals` (recorded vendor JSON bodies; synthetic unsupported values) |
| CDX-4.3 | use the wording lists only for the class `other` or a missing class, and mark the error as decided by wording | DRV-4.4 | Changed | `C26`; `RunErrors.test_structured_classes_never_use_wording_fallback`, `RunErrors.test_exact_wording_lists_removed_fragments_and_tool_version` |
| CDX-4.4 | emit a `notice` for every `error` notification whose `willRetry` is true | DRV-4.12 | New | `C28`; `RunErrorEvents.test_each_retry_emits_notice_and_first_credential_refusal_is_remembered`; fresh `probe.errors` (unreachable proxy; retries continue until caller stop) |
| CDX-4.5 | stop the run at the first retry notification with status 401 or 403 and finish it as `credential_rejected` | DRV-4.8 | New | `C4`, `C28`; `ErrorRuns.test_rejected_retry_before_turn_start_reply_interrupts_accepted_turn`, `ErrorRuns.test_rejected_unknown_child_retry_is_replayed_after_spawn_discovery` |
| CDX-4.6 | keep the latest `account/rateLimits/updated` of a run and store it as the Subscription's usage report when the run ends, without losing values the notification lacks | DRV-4.13 | New | `C30`; `RunUsage.test_sparse_notifications_preserve_stored_fields_and_latest_values`, `RunUsageStorage.test_persist_preserves_concurrent_fields_and_compatible_record`, `RunUsageStorage.test_late_report_does_not_restore_account_or_overwrite_newer_usage`; fresh `live.errors-usage` on `test-chatgpt` |
| CDX-4.7 | on a `rate_limited` failure, ask the tool once for the account's limits before ending the process and take the wait from the exhausted window | DRV-4.5 | New | `C27`; `RunUsage.test_wait_requires_current_vendor_exhaustion_and_reset_without_cache_guessing`; reached-limit failures remain synthetic, not observed live |
| CDX-4.8 | treat every notification as a sign of life | DRV-4.9 | New | `C29`; `RunClockTests.test_any_notification_resets_idle_and_zero_disables_it`, `RunClockTests.test_total_limit_is_independent_of_notifications_and_work`; fresh `probe.errors` |
| CDX-4.9 | report a process that ends before `turn/completed` as `tool_failed`, with at most 1 KiB from the end of its log | DRV-4.2 | Changed | `C26` (exit), `C42`; `AppServerTests.test_malformed_oversized_boolean_id_exit_and_internal_request_timeout`, `AppServerTests.test_authentication_rejection_is_specific_and_diagnostics_are_bounded`; `RunErrors.test_safe_bounded_messages_and_details_without_raw_vendor_response` |
| CDX-4.10 | read the tool's version from the handshake and fail the run on a version below the oldest supported one | DRV-4.14 | Changed | `C26` (old handshake), `C31`; `AppServerTests.test_handshake_version_and_effective_configuration_are_enforced`; fresh probe/live `started.toolVersion` |

## Python migration verification on 7 October 2026

SYL-95 preserved the then-implemented generic failed-turn result, account RPC rejection, request timeouts, bounded transport diagnostics and vendor-version preflight in Python. SYL-90 subsequently verified advanced tools; SYL-91 adds the complete error mapping, retry interruption, run-derived limit reports and run clocks, with `C4` and `C26`–`C30` in the errors wrapper. Complete development checks remain SYL-92, and the first working numbered Codex Build remains SYL-94.

Current names of the form `Class.method` refer to unittest methods under `tests/`, run on pinned CPython 3.14.8 from source, the standalone development candidate and its relocated copy. Evidence: `research/python-migration-2026-10-07/verification.json`, `research/python-migration-2026-10-07/packaged-unit.txt`, `research/python-migration-2026-10-07/scoped-conformance-base.txt`, `research/python-migration-2026-10-07/scoped-conformance-runs.txt`, `research/python-migration-2026-10-07/no-prompt-probes.json` and `research/python-migration-2026-10-07/standalone-rehearsal.json`. The real migration probes sent no prompts. Dated vendor failure and retry observations in this document remain historical schema/probe evidence and do not establish fresh Python live handling; unobserved vendor failures below remain unobserved.

## SYL-91 verification on 7 October 2026

The active Python implementation passes the Codex error-table rows in `C26`, waits and one post-limit read in `C27`, immediate credential stopping in `C28`, start/idle/total clocks and waiting work in `C29`, and sparse run usage in `C30`. `C4` covers run rejection and account recovery. Focused integration tests also cover a retry before turn/start replies, a child rejection before discovery, and bounded cleanup with blocked output. Caller questions are unsupported for Codex and remain checked by `C25`; the question-open idle fixture applies to Claude.

Fresh `probe.errors` on codex-cli 0.159.2 used only `test-chatgpt`, a clean environment and an unreachable loopback proxy. Two retry notices arrived, the run remained active, and caller stop finished cancelled with scratch and record cleanup. The proxy prevented vendor access and spent no quota. Fresh `live.errors-usage` sent one no-tools `Reply exactly OK.` request on `test-chatgpt`, `gpt-5.6-luna`, low effort: completed, run-derived usage stored and sparse fields preserved. The reported weekly usage stayed at 46 percent; output usage was 5 tokens. Evidence, including initial failed offline runs and their corrections, is in `research/errors-2026-10-07/`. These checks do not claim observation of a vendor limit or overload.

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
| CDX-D23 | What does the classification basis mean when no wording phrase matches? | Use fields for a structured class or a parsed vendor status/model/effort refusal. For other or a missing class, wording means the permitted text fallback was consulted, even when no phrase matched and the result stays vendor_error. Bare 401, 429, quota and unauthorized never match | Decided 7 October 2026 during SYL-91, a technical clarification; RunErrors.test_exact_wording_lists_removed_fragments_and_tool_version and C26 |
| CDX-D24 | How are run clocks and sparse usage updates coordinated with stopping? | Start the monotonic 60-second budget when the app-server starts; each startup RPC keeps its own 30-second bound. Every notification resets idle, running calls suspend it, and caller idle/total seconds are never test-scaled. A reached limit or credential refusal uses normal interrupt and cleanup but finishes failed. Treat absent and null limit fields as unavailable; preserve fuller stored fields, merge under the account lock and protect a newer login or usage report. A rate-limited run makes exactly one limits read, and uses only an explicitly exhausted window and stated reset for its wait | Decided 7 October 2026 during SYL-91, a technical choice; C27, C28, C29, C30, RunClockTests, RunUsage and RunUsageStorage |
