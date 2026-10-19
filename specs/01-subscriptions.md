---
role: authored
spec: CDX-1
status: accepted
---
# Codex Driver · 01 Subscriptions

How the Codex Driver meets [DRV-1](../../arbol/driver-contract/01-subscriptions.md) with the `codex` command-line tool. It serves one vendor family, ChatGPT accounts, and does all account work through the tool's app-server running in the tool's default home, `~/.codex`, on the owner's own sign-in of `codex` (DRV-D42). It matters because version 1 had no account handling on this route at all: a turn ran as whoever was logged in to the tool on the machine, whatever Arbol showed. The Driver runs on that same sign-in again, but it checks it, reports it and offers its sign-in.

## Scope

Covered: the `chatgpt` family, the home and environment the tool is given, sign-in and sign-out, status checks, usage, the model catalog.

Not covered: the contract itself (DRV-1); threads, turns and the configuration a run starts the app-server with (CDX-2); approvals and sandbox settings (CDX-3); recognising a rate limit or a rejected login in the output of a run (CDX-4).

## Behaviour

### Family

| Family | Vendor | Sign-in | Settings |
|---|---|---|---|
| `chatgpt` | OpenAI | The owner's own sign-in of `codex`, in `~/.codex/auth.json` | None |

The family has one Subscription, `chatgpt`. `subscriptions create` refuses a second with `invalid_input`: `codex` has no tested way to run as another account than the one signed in to `~/.codex`, and changing `auth.json` would change the account of every other `codex` on the Mac ([DRV-0](../../arbol/driver-contract/00-overview-and-boundary.md#the-vendor-tools-home)).

Not offered in the first release: key-billed OpenAI accounts and the cloud-provider logins the tool's protocol also lists.

Observed in version 1: one built-in ChatGPT account. Two routes drew on it: the vendor tool route, and a direct client for the ChatGPT backend that is retired.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:daemons/core/arbol_core/subscriptions.py#DEFAULT_SUBSCRIPTIONS`
- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Concept model`

### Home and environment

The Driver starts every child process of `chatgpt` in the tool's default home, `~/.codex`, as the Leather Bag starts `codex` by hand. It sets no `CODEX_HOME`. The tool keeps the owner's sign-in and configuration there. The Driver writes nothing in that folder: no configuration file of its own, no copy, no change. The settings it needs for a run are options of that run's command line (CDX-2). It never reads the sign-in the tool stores there.

The environment of a child process starts from an allow-list of inherited variables (home, path, user, locale, temporary directory, proxy and certificate settings). Nothing named `OPENAI_*` or `CODEX_*` is inherited, so an inherited `CODEX_HOME` is removed.

When an app-server starts, its answer to the opening handshake names the home it uses. The Driver compares that with `~/.codex` and stops the process when they differ.

Only the test Subscription `test-chatgpt` of probes and live checks keeps a home of its own, in the test state directory and readable by the owner only. It is passed as `CODEX_HOME`, so a probe never starts the tool in `~/.codex` ([DRV-D44](../../arbol/driver-contract/05-conformance.md#decisions)).

Observed until 19 October 2026: every Subscription had a folder of its own in the state directory, passed to the tool as `CODEX_HOME`. The Driver wrote the tool's configuration there, and the tool kept the Subscription's login there.

Observed in version 1: the tool route injected no credential and did not redirect the tool's home. A turn ran with the home the service inherited, normally the Leather Bag's own `~/.codex`, login and configuration included. Because that configuration was not Arbol's, a turn was refused when it contained settings Arbol could not represent. The account bound to the route served only to attribute usage and to select a model list.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Account profiles for the Claude tool`
- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Can two accounts of one vendor run at the same time, isolated?`
- `arbol_deprecated_v1:daemons/core/arbol_core/subscriptions.py#DEFAULT_IP_BINDINGS`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#codex_home`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#validate_config`

### Signing in and out

Proposed. The Driver starts an app-server in `~/.codex` and asks it to log in. Signing `chatgpt` in is signing `codex` in on this Mac, for every session of it.

| Contract step | App-server exchange |
|---|---|
| Sign-in on this machine | Request `account/login/start` with type `chatgpt`. The answer carries an authorisation address and a login identifier; the Driver returns `open_url` with that address |
| Sign-in from another device | Request `account/login/start` with type `chatgptDeviceCode`. The answer carries a verification address and a user code; the Driver returns `open_url` with both |
| Completion | Notification `account/login/completed` with `success` true: the Driver reads the account and returns `done`. With `success` false: `failed`, carrying the tool's error text |
| Cancel, replacement, time-out | Request `account/login/cancel` with the login identifier, then the app-server is stopped |
| Sign-out, removal | Refused for `chatgpt` with `invalid_input`, and the message says to sign out in `codex` itself ([DRV-D43](../../arbol/driver-contract/01-subscriptions.md#decisions)). `account/logout` would sign out every `codex` on the Mac, the owner's own included. In the home of the test Subscription the request stays `account/logout` |

The app-server stays running while a sign-in is pending, because it is the tool that receives the vendor's callback. The Driver holds no ChatGPT credential and renews none; the tool does both.

Only one sign-in on this machine can be pending at a time, across all homes, because the tool receives the callback on one fixed local address. The Driver therefore lets one such sign-in be pending across all its Subscriptions, and reports a sign-in that another login on the machine has ended as `failed` with that reason. The device-code sign-in has no such limit.

Observed with the installed tool on 5 October 2026: the authorisation address is on `auth.openai.com` and the tool listens on `127.0.0.1:1455` while the sign-in is pending. The tool does not open a browser itself, so the caller's window can show the page. A second sign-in started in another home succeeded and ended the first with "Login cancelled". The device-code answer carries the address `https://auth.openai.com/codex/device` and a code of the form `XXXX-XXXXX`.

`chatgpt` uses the owner's own sign-in in `~/.codex` where it is: nothing is copied. When `codex` is signed in already, `sign-in` starts no login: it reads the account and answers `done` (CDX-D27). For example, the owner has signed `codex` in by hand; `arbol-codex-driver subscriptions sign-in chatgpt` then answers `done` with the account's e-mail address and plan, and `auth.json` stays as it is.

Observed until 19 October 2026: the existing login in `~/.codex` was not taken over, and a Subscription was signed in once, in its own home (CDX-D2).

Observed in version 1: no in-app sign-in existed. The Leather Bag ran the tool's login in a terminal; "Check login" then copied the newest of two credential files from the home directory into Arbol's Keychain. The copy went stale as soon as the tool renewed its login, and Arbol's recovery was to copy again. Signing out in Arbol deleted the copy and left the tool logged in, so the route kept working.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:daemons/core/arbol_core/universe_import.py#read_universe_auth`
- `arbol_deprecated_v1:daemons/core/arbol_core/universe_import.py#import_from_auth_json`
- `arbol_deprecated_v1:daemons/core/arbol_core/rpc/subscription.py#_login`
- `arbol_deprecated_v1:daemons/core/arbol_core/orchestration/agent_attempt_execution.py#AgentAttemptExecutionService._refresh_bound_subscription_token`
- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Sign-in and sign-out`

### Status check

`check` starts an app-server in the home and sends `account/read` with `refreshToken` set, which makes the tool renew its login with the vendor before answering. An account of type `chatgpt` means `signed_in`; its e-mail address and plan are stored with the Subscription. No account means the login is gone: a Subscription that was `signed_in` moves to `needs_attention` with the remedy "sign in again". Any other account type in the home is reported as `needs_attention` as well, because this family only covers ChatGPT logins.

Observed with the installed tool: without `refreshToken` the request is answered at once from the home, without contacting the vendor; with it, the answer took about a second and the login file was rewritten.

Observed in version 1: the accounts page's Test passed for a ChatGPT route when the row said logged in, without contacting the vendor or the tool.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Intelligence Provider settings`

### Usage

One request `account/rateLimits/read` to an app-server in the home. The answer carries up to two windows, each with a used percentage and optionally a length in minutes and a reset time in seconds since 1970. Which window is which is read from its length, not from its place in the answer.

| Usage report field | Taken from |
|---|---|
| Window of kind `weekly` | A window of 10,080 minutes |
| Window of kind `session` | A window of 300 minutes |
| Window of kind `other` | A window of any other length |
| `label` | "5-hour window" for 300 minutes, "Weekly window" for 10,080 minutes, otherwise the length in hours or days |
| `usedPercent`, `windowMinutes`, `resetsAt` | `usedPercent`, `windowDurationMins`, `resetsAt` |
| `limitReached` | True when the window is used to 100 percent |
| `plan` | The plan type in the answer, else the one from the status check |
| `detailsUrl` | `https://chatgpt.com/codex/settings/usage` |
| `extra` | Whether ordinary use is still allowed, the reason a limit was reached, the credit balance, and the limits listed per limit identifier, as the tool reports them |

When the tool cannot produce an answer, the outcome is `unavailable` with the tool's message.

Observed with the installed tool: the probed account had one window, the weekly one, in the place called primary, used to 100 percent, with the second place empty. With credits on the account, runs continued and the credit balance fell; no limit error occurred.

Observed in version 1: usage was read from an undocumented address of the ChatGPT backend with the copied token, with request headers imitating the vendor tool at a fixed version, over a connection to a fixed network address. The shown values were the same: primary and secondary window, plan, a link to the vendor's limits page.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:daemons/core/arbol_core/universe_usage.py#normalize`
- `arbol_deprecated_v1:daemons/core/arbol_core/universe_usage.py#build_headers`
- `arbol_deprecated_v1:daemons/core/arbol_core/rpc/subscription.py#_codex_usage`

### Model catalog

Requests `model/list` to an app-server in the home, following the cursor until the list ends. Hidden models are not asked for. Source `tool`. The service tiers the tool lists for a model go into `serviceTiers`.

| Catalog field | Taken from |
|---|---|
| `id` | `id` |
| `label`, `description` | `displayName`, `description` |
| `efforts` | The `reasoningEffort` of each entry in `supportedReasoningEfforts` |
| `defaultEffort` | `defaultReasoningEffort` |
| `isDefault` | `isDefault` |

When the request fails the Driver answers with its built-in ChatGPT list, source `builtin`.

Observed with the installed tool: the list is one page of eight models when hidden ones are left out, each with its efforts and service tiers. `id` and `model` were equal for every entry. Without a login the request still answers, with another list; the Driver asks only for a Subscription that is `signed_in` (DRV-1.11).

Observed in version 1: the list was read from the ChatGPT backend with the copied token. The backend reveals newer model families only to a recent enough client, so Arbol reported the version of the installed tool; reporting a newer one offered models the tool then rejected in the middle of a turn. Review-only and non-selectable entries were dropped. Asking the tool itself removes the version question: the tool lists what it can run.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:daemons/core/arbol_core/provider_models.py#fetch_codex_models`
- `arbol_deprecated_v1:daemons/core/arbol_core/provider_models.py#installed_codex_client_version`
- `arbol_deprecated_v1:daemons/core/arbol_core/provider_models.py#_arbol_is_special_purpose_codex_model`

## SYL-92 verification, 7 October 2026

SYL-92 passed the complete 38-scenario shared registry for both Python Drivers. Codex also passed 128 unit methods, Ruff and strict mypy from source; its standalone CPython 3.14.8 development candidate passed the same units and all 38 scenarios, and its relocated copy passed metadata and unit checks under a minimal environment. A fresh packaged `dev probe` passed against codex-cli 0.159.2 with zero inference requests. The packaged build gate sent exactly one no-tools ready message through `test-chatgpt`; it completed and reported tokens and usage before/after. The extended five-turn `dev live-check` orchestration and refusal gates passed offline, but the extended vendor run was not requested. Contract and state format remain 1. The first numbered Codex Build is the separate SYL-94 task.

Current records and source/package provenance: `~/Artifacts/arbol-codex-driver/research/conformance-2026-10-07/verification.json`, `coverage-audit.json`, `packaged-probe.json` and `packaged-build-check.txt` in that folder. Dated migration and TypeScript evidence below remains historical; unobserved real vendor failures remain unobserved. The coverage audit retains every former Verified by cell before this update.

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-1.1 | offer the family `chatgpt` (vendor login, no settings), with one Subscription from the start, named `chatgpt`, which is the default | DRV-1.1 | Kept | Codex Python: `C1`, `C10`, `Accounts.test_local_concurrent_creation_update_preserves_owner_settings_and_remove_isolated` |
| CDX-1.2 | set no `CODEX_HOME` for a child process of `chatgpt`, so that the tool runs in `~/.codex` on the owner's own sign-in; pass a home of its own, readable by the owner only, only for the test Subscription of probes and live checks; refuse to create a second Subscription of the family with `invalid_input` | DRV-1.2 | Changed | unit; contract |
| CDX-1.3 | stop an app-server whose handshake answer names another home than `~/.codex`, or than its own home for the test Subscription | DRV-1.2 | New | unit |
| CDX-1.4 | build each child's environment from an allow-list; no inherited `OPENAI_*` or `CODEX_*` variable reaches the tool | DRV-0.5 | Changed | Codex Python: `C8`, `AppServerTests.test_private_home_configuration_clean_environment_and_owner_cleanup`, `Foundation.test_arguments_settings_environment_and_error_sanitization` |
| CDX-1.5 | write nothing in `~/.codex`: no configuration file of its own, no copy, no change. Give the settings a run needs as options of its command line (CDX-2.2), and read nothing there but what CDX-3.14 names | DRV-0.4 | Changed | contract; probe |
| CDX-1.6 | sign in only through the app-server's `account/login/start` and `account/login/cancel`, and hold no ChatGPT credential itself. Refuse sign-out and removal of `chatgpt` with `invalid_input`; send `account/logout` only in the home of the test Subscription | DRV-1.8 | Changed | unit; contract |
| CDX-1.7 | offer both the sign-in on this machine and the device-code sign-in, the second when `sign-in` is called with `--by-code` | DRV-1.5 | New | Codex Python: `C2`, `Accounts.test_login_replacement_cancels_pending_and_sign_out_clears_credentials` |
| CDX-1.8 | keep the app-server of a pending sign-in running until the tool reports completion, the attempt is cancelled or it times out, and leave no process behind afterwards | DRV-0.10 | New | Codex Python: `C2`, `C6`, `AppServerTests.test_cancelled_request_leaves_transport_available_and_preabort_sends_nothing`, `AppServerTests.test_cleanup_survives_capture_failure_and_ends_ignoring_descendant`, `AppServerTests.test_startup_wrong_home_config_and_cancellation_gives_eof_before_force` |
| CDX-1.9 | never read, copy or log the login the tool stores in a home | DRV-1.3 | Changed | Codex Python: `C7`, `Accounts.test_unsigned_refusals_and_malformed_state_do_not_start_vendor_or_disclose_contents` |
| CDX-1.10 | check a Subscription with `account/read` and a renewal of the login, and move it to `needs_attention` when the home holds no ChatGPT account | DRV-1.7 | Changed | Codex Python: `C4`, `C28`, `Accounts.test_usage_last_good_cache_rejection_and_catalog_fallback`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` |
| CDX-1.11 | build the usage report from `account/rateLimits/read` by the table above | DRV-1.17 | Changed | Codex Python: `C41`, `Accounts.test_usage_last_good_cache_rejection_and_catalog_fallback`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` |
| CDX-1.12 | build the model catalog from `model/list`, all pages, without hidden models | DRV-1.20 | Changed | Codex Python: `C41`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` |
| CDX-1.13 | make no request of its own to a ChatGPT or OpenAI address | DRV-1.19 | Changed | Codex Python: `C41`, `AppServerTests.test_private_home_configuration_clean_environment_and_owner_cleanup` |
| CDX-1.14 | let only one sign-in on this machine be pending across all its Subscriptions, and report a sign-in ended by another login on the machine as `failed` with that reason | DRV-1.5 | New | Codex Python: `C2`, `Accounts.test_login_replacement_cancels_pending_and_sign_out_clears_credentials` |
| CDX-1.15 | read a usage window's kind from its length | DRV-1.17 | New | Codex Python: `C41`, `Foundation.test_catalog_pagination_fallback_usage_and_unknown_identifiers` |

## Python migration verification on 7 October 2026

The historical SYL-95 checks ran on pinned CPython 3.14.8. Names of the form `Class.method` in the table above identify unittest methods under the repository’s `tests/` directory, exercised from source and from the standalone development candidate. The candidate carries 62 unit methods; its interpreter and fixtures also run after relocation to a path containing spaces. That migration candidate was partial; SYL-90, SYL-91 and SYL-92 subsequently completed those implementation checks. The first working numbered Codex Build remains SYL-94.

The retained subscription wrapper invokes `C1` “Local Subscription records”, `C2` “Sign-in steps, replacement and expiry”, `C6` “Cancelling and killing a pending sign-in”, `C39` “Two accounts of one family stay independent” and `C41` “Usage, model catalogs and vendor account details”. Its limited scenarios retain their original scopes: `C4` is subscription check rejection and recovery only; `C5` is sign-out, account clearing and home removal only; `C7` is subscription operations and tool-owned login only; `C8` is sign-in, status, usage and catalog children only; `C40` is unsigned models, check and usage only. Only executable selection changed in the wrapper.

Evidence: `research/python-migration-2026-10-07/verification.json`, `research/python-migration-2026-10-07/packaged-unit.txt`, `research/python-migration-2026-10-07/scoped-conformance-subscriptions.txt`, `research/python-migration-2026-10-07/compatibility.json`, `research/python-migration-2026-10-07/no-prompt-probes.json` and `research/python-migration-2026-10-07/standalone-rehearsal.json`. The compatibility checks exercise TypeScript-to-Python and Python-to-TypeScript account reads, writes and removals, including concurrent creation. The migration’s real-tool checks are version, account, usage, catalog and private-configuration probes without prompts; they do not establish new browser consent or live inference.

### Historical TypeScript verification

The retired TypeScript runner `test/probe-subscriptions.mjs` against installed `codex-cli` 0.159.2 sent no prompts. Its sanitized record is `research/subscriptions-2026-10-07.json` (`probe.subscriptions` and `live.subscriptions`). Fresh homes accepted the Driver configuration and reported it through `config/read`; both login methods returned their page addresses, and device sign-in returned a code. A second local login cancelled the first; cancellation and logout worked. The real app-server exited after its input pipe closed. On the existing signed-in `test-chatgpt` home, the Driver commands `check`, `usage` and `models` returned a signed-in account, an `ok` usage report and a tool catalog of seven models, including efforts and service tiers. No credential file was read or copied. New browser consent was not repeated, and the signed-in test account was not logged out. Browser completion remains the real observation of 6 October below.

Before the migration, `test/conformance-subscriptions.mjs` passed C1, C2, C6, C39 and C41 plus the same subscription portions of C4, C5, C7, C8 and C40. The former TypeScript check `subscriptions.active-run` exercised sign-out/removal against valid DRV-6 run records. Those historical results do not enlarge the retained subscription scopes; current run, continuity and stopping coverage is recorded in CDX-2 and in the migration evidence.

## Probes recorded

Run on 5 October 2026 against `codex-cli` 0.159.2, with a clean environment and no prompt sent.

| Probe | Result |
|---|---|
| `codex login status`, default home | "Logged in using ChatGPT" |
| `codex login status`, `CODEX_HOME` set to an empty folder | "Not logged in", exit code 1. The login is kept per home |
| `ls ~/.codex` | The login is a file, `auth.json`, readable by the owner only. No setting chooses another store |
| `codex app-server generate-json-schema` | The protocol lists the requests `account/read`, `account/login/start`, `account/login/cancel`, `account/logout`, `account/rateLimits/read`, `account/usage/read`, `model/list` and the notifications `account/login/completed`, `account/updated`, `account/rateLimits/updated` |
| Shapes in that schema | Login types `chatgpt` (answer: `authUrl`, `loginId`) and `chatgptDeviceCode` (answer: `verificationUrl`, `userCode`, `loginId`). Account of type `chatgpt`: `email`, `planType`. Rate-limit window: `usedPercent`, `windowDurationMins`, `resetsAt`. Model: `id`, `model`, `displayName`, `description`, `hidden`, `isDefault`, `defaultReasoningEffort`, `supportedReasoningEfforts`. Handshake answer: `codexHome` |

A second round of probes on the same day used real requests and turns; it is recorded in the [probe record](../research/tool-probes-2026-10-05.md), and what it showed about accounts is stated in the sections above.

Observed on 6 October 2026, in one real sign-in by the owner in a new home, in a browser window that was not the system browser: after `account/login/start` with the type `chatgpt` the page went from `auth.openai.com` to the tool's listener on `127.0.0.1:1455`. The tool then sent `account/login/completed` with `success: true` and `account/updated`. `account/read` reported an account of type `chatgpt` with its e-mail address and plan. The home held `auth.json`, readable by the owner only. `account/rateLimits/read` answered at once, for an account below its limit: one window of 10,080 minutes with the share used and the reset time, `ordinaryUsageAllowed: true`, and no credits.

Not established:

- every host the ChatGPT sign-in page visits after `auth.openai.com`, needed for the host list of `open_url`. Until a real sign-in has shown them, the list is `auth.openai.com` and `127.0.0.1`, where the tool listens for the return;
- a five-hour window: the answer held one window only, the weekly one;
- whether the tool, told to keep its login in the system keychain, still keeps one login per home. The setting is accepted; no login was made with it.

## Known problems in version 1

Not to be reproduced.

- **The route ran as the machine's login.** No credential was injected and the tool's home was not redirected. Two ChatGPT accounts could not run side by side, signing out in Arbol did not stop the route, and the usage shown could belong to another account than the one doing the work. Since 19 October 2026 the Driver runs on that login again, by the owner's decision (DRV-D42). What is not reproduced is the rest: the Driver reports the account `codex` is signed in with, reads the usage of that account, and refuses a sign-out it cannot carry out.
- **A rotating login was copied.** See DRV-1.
- **The vendor's backend was imitated.** Usage and model list were read from undocumented addresses with the tool's headers and a version number that had to be kept in step by hand.
- **The Leather Bag's configuration decided whether a turn could start.** A custom model provider, a saved permission or network profile and similar settings in `~/.codex` made Arbol refuse the turn.

Historical evidence (frozen version 1; ordinary locators, not Source Refs):

- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Can two accounts of one vendor run at the same time, isolated?`
- `arbol_deprecated_v1:product-spec/05-intelligence-providers.md#Known problems and lessons`
- `arbol_deprecated_v1:daemons/core/arbol_core/provider_models.py#_arbol_fetch_codex_models_payload`
- `arbol_deprecated_v1:drivers/codex/arbol_driver_codex/session.py#validate_config`

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D27 | `codex` is already signed in in `~/.codex` when `sign-in` is called for `chatgpt`. Does the Driver start a login? | No. It first sends `account/read`. With a ChatGPT account in `~/.codex` it stores the account's details and answers `done` at once, so a sign-in through Arbol never replaces the owner's own. Only without one does it start `account/login/start`. The other choice starts a login every time, and a sign-in with another ChatGPT account would change the account of every `codex` on the Mac | Open: technical consequence of DRV-D42, proposed 19 October 2026 |
| CDX-D14 | How are account RPCs, sign-in races and configuration checked? | One JSONL app-server per operation, with a 30-second request bound, buffered login notifications and a process group of its own. Write the Driver configuration, verify it with config/read, and compare real home paths in initialize. Publish a sign-in reservation with an attempt token and by-code flag under the Subscription lock; a replacement sets stopReason before signalling. Local sign-ins in one state directory choose the latest process identity among simultaneous reservations; the vendor reports a local login ended from another state directory or program. Each network answer updates only the login state and checkedAt revision it originally checked. The five-minute sign-in bound covers startup, login and the final account read | Decided 7 October 2026 during SYL-81, a technical choice. Changed on 19 October 2026 by DRV-D42: no configuration is written; the run's options are verified with config/read (CDX-D28), and the home compared in initialize is `~/.codex`. No credentials are read by the Driver and no direct vendor HTTP client is used; current Python checks: `C2`, `C6`, `AppServerTests.test_timeout_and_cancellation_include_blocked_stdin_drain`, `AppServerTests.test_startup_wrong_home_config_and_cancellation_gives_eof_before_force` and `Accounts.test_login_replacement_cancels_pending_and_sign_out_clears_credentials`. Earlier probe/live names are historical TypeScript evidence |
| CDX-D1 | Where does the tool keep a Subscription's login: its file in the home, or the system keychain? | The file, as the tool does by default: it is proven to be per home. The keychain would match the rule that secrets live only there, and is preferred once a probe shows it is also per home | Decided 6 October 2026, left to Claude by the owner: the file. `codex` keeps a Subscription's login in `auth.json` in its home, readable by the owner only, as it does for everyone who uses it. No move to the keychain is planned (SYL-35). Since 19 October 2026 (DRV-D42) the login of `chatgpt` is the owner's own, kept where the owner's setup of `codex` keeps it; the Driver gives no `cli_auth_credentials_store` (CDX-D28) |
| CDX-D2 | Should an existing login in `~/.codex` be taken over? | No. Copying it reproduces version 1's stale-copy defect; the Leather Bag signs in once per Subscription | Decided 6 October 2026 by the owner: the proposed default. A Subscription is signed in properly, which the Driver also needs to report the account's limits (SYL-63). Superseded on 19 October 2026 by DRV-D42: `chatgpt` uses the owner's own sign-in in `~/.codex` where it is. Nothing is copied, so version 1's stale copy does not return |
| CDX-D3 | Which sign-in does the caller offer first? | The sign-in on this machine; the device code as the alternative, for a machine that cannot open the vendor's page | Decided 6 October 2026 by the owner: the proposed default (SYL-64) |
