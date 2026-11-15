---
role: authored
spec: CDX-1
status: accepted
---
# Codex Driver · 01 Subscriptions

How the Codex Driver meets [DRV-1](../../arbol/driver-contract/01-subscriptions.md) with the `codex` command-line tool. It serves one vendor family, ChatGPT accounts, and does all account work through the tool's app-server running in the tool's default home, `~/.codex`, on the owner's own sign-in of `codex` (DRV-D42). It matters because version 1 had no account handling on this route at all: a turn ran as whoever was logged in to the tool on the machine, whatever Arbol showed. The Driver runs on that same sign-in again, but it checks it, reports it and offers its sign-in.

## Current qualification selection · 12 November 2026

Current qualification uses only an already registered, signed-in real Subscription and its existing native state/home binding. Test profiles are prohibited. Verify the actual existing profile before live launches; do not create, alias, copy or sign in a profile, and do not redirect its credentials into disposable state. Normal vendor refresh and ordinary uniquely identified run/continuity metadata remain allowed. Keep application databases, runtime, Build registries and raw evidence private and separate. This supersedes the mandatory `test-chatgpt`/test-state selection in earlier qualification instructions while retaining those earlier descriptions, decisions and observations as history. The active shared rule is [DRV-5](../../arbol/driver-contract/05-conformance.md); current CLI selection is documented in the code repository's `TESTS.md`.

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

<!-- sources:
arbol-codex-driver:src/arbol_codex_driver/environment.py#clean_environment
arbol-codex-driver:src/arbol_codex_driver/app_server.py#AppServer.start
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.app_server_home
-->

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

<!-- sources:
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.create
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.sign_in
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.sign_out
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.remove
arbol-codex-driver:src/arbol_codex_driver/cli.py#main
-->

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
| `resource` | Absent. The app server's `RateLimitWindow` carries `usedPercent`, `windowDurationMins` and `resetsAt` and names no unit, so the Driver does not guess what a window counts (DRV-1.27, CDX-D31). The credit balance beside the windows is the account's, not a window's unit, and stays in `extra` |

When the tool cannot produce an answer, the outcome is `unavailable` with the tool's message.

Observed with the installed tool: the probed account had one window, the weekly one, in the place called primary, used to 100 percent, with the second place empty. With credits on the account, runs continued and the credit balance fell; no limit error occurred.

Observed on 26 October 2026 with `codex-cli` 0.162.1, in the protocol schema the tool generates without a prompt ([the probe record](../research/app-server-rate-limit-schema-2026-10-26.md)): no field of a rate-limit window or snapshot names what the window counts.

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
| CDX-1.16 | leave `resource` absent on every usage window while the app server names no unit for a window, and never guess it (CDX-D31) | DRV-1.27 | New | Codex Python: `C41`, `C30`, `Foundation.test_usage_windows_carry_no_resource_the_app_server_does_not_state`; probe: `research/app-server-rate-limit-schema-2026-10-26.md` |

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
| CDX-D31 | Does a Codex usage window say what it counts (DRV-1.27)? | No. The app server's `RateLimitWindow` has `usedPercent`, `windowDurationMins` and `resetsAt` only, and the snapshot's `credits` is the account's credit balance, not a window's unit; the tool speaks of "usage" and names no token, message or request count anywhere in its usage answer. So `resource` stays absent rather than guessed; the mapping is revisited when a schema field names a unit | Decided 26 October 2026 during SYL-292, a technical choice; the probe is [`research/app-server-rate-limit-schema-2026-10-26.md`](../research/app-server-rate-limit-schema-2026-10-26.md) on `codex-cli` 0.162.1 |

## Browser lifetime proof refinement · 14 November 2026

The shared [revision-1 local proof](../../arbol/driver-contract/01-subscriptions.md#local-subscription-lifetime-proof--browser-amendment-14-november-2026) and [format-2 maintenance boundary](../../arbol/driver-contract/06-state-and-simultaneous-calls.md#identity-format-2-and-maintenance-boundary--14-november-2026) are specified technical means for BRW-1.11/.14. This amendment is unimplemented and has no historical qualification credit.

The default canonical selector is `chatgpt`; identity must materialize its witness independently from the format-file birth/ctime used by the current implicit record. The strict `parse_record` whitelist remains the old public/private record shape; use the format-2 sidecar. Preserve the production single-account limit and refusal to sign out/remove `chatgpt`, including force. Existing isolated historical test selectors are not authorized provider qualification profiles. Identity is local even when signed out and does not call app-server or read `~/.codex`.

ABR-34 must inspect `state.py`, `subscriptions.py`, `cli.py`, `arguments.py` and every auth/usage/run completion writer before deriving its exact territory. The existing `Subscriptions.remove` and sign-in progress protocol must map successful permitted removal/ambiguous crash to the sidecar journal without transplanting proof. Capability is per exact Build, not inferred from contract number.

<!-- sources:
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.record
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#parse_record
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.remove
arbol-codex-driver:src/arbol_codex_driver/state.py#State
arbol-codex-driver:src/arbol_codex_driver/identity_protocol.py#PrivateDirectory
arbol-codex-driver:src/arbol_codex_driver/identity_protocol.py#canonical_bytes
arbol-codex-driver:src/arbol_codex_driver/identity_protocol.py#parse_bytes
arbol-codex-driver:src/arbol_codex_driver/payload.py#verify_payload
arbol-codex-driver:src/arbol_codex_driver/payload.py#verify_authority
arbol-codex-driver:src/arbol_codex_driver/payload.py#bootstrap_entry
arbol-codex-driver:src/arbol_codex_driver/process_identity.py#process_identity
arbol-codex-driver:src/arbol_codex_driver/process_identity.py#boot_uuid
arbol-codex-driver:src/arbol_codex_driver/admission.py#admit
arbol-codex-driver:src/arbol_codex_driver/admission.py#Session
arbol-codex-driver:src/arbol_codex_driver/app_server.py#startup_ledger
arbol-codex-driver:src/arbol_codex_driver/maintenance.py#Maintenance
arbol-codex-driver:src/arbol_codex_driver/maintenance.py#Maintenance.recheck
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation.upgrade
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation.reset
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation.recover
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation.prepare_restore
arbol-codex-driver:src/arbol_codex_driver/state_upgrade.py#Operation.restore
arbol-codex-driver:src/arbol_codex_driver/cli.py#Invocation
arbol-codex-driver:src/arbol_codex_driver/cli.py#main
arbol-codex-driver:src/arbol_codex_driver/cli.py#entry
arbol-codex-driver:src/arbol_codex_driver/build.py#qualified_capabilities
arbol-codex-driver:src/arbol_codex_driver/build.py#build_identity
arbol-codex-driver:scripts/identity_package.py#emit
arbol-codex-driver:scripts/identity_package.py#inventory
arbol-codex-driver:scripts/identity_package.py#validate_links
arbol-codex-driver:scripts/build_support.py#source_provenance
arbol-codex-driver:scripts/build_support.py#committed_snapshot
arbol-codex-driver:scripts/package_build.py#package
arbol-codex-driver:src/arbol_codex_driver/state.py#with_subscription_directory_lock
arbol-codex-driver:src/arbol_codex_driver/state.py#read_lock
arbol-codex-driver:src/arbol_codex_driver/runs.py#Runs.orphan_groups
arbol-codex-driver:src/arbol_codex_driver/identity.py#RecoveryObservation
arbol-codex-driver:src/arbol_codex_driver/identity.py#retire_pending
arbol-codex-driver:src/arbol_codex_driver/maintenance.py#admit
arbol-codex-driver:src/arbol_codex_driver/identity.py#IdentityState
arbol-codex-driver:src/arbol_codex_driver/identity.py#root_generation
arbol-codex-driver:src/arbol_codex_driver/identity.py#expected_proof
arbol-codex-driver:src/arbol_codex_driver/identity.py#IdentityState.capture_proof
arbol-codex-driver:src/arbol_codex_driver/identity.py#PendingIdentity
arbol-codex-driver:src/arbol_codex_driver/identity.py#IdentityJournal
arbol-codex-driver:src/arbol_codex_driver/identity.py#LifetimeSnapshot
arbol-codex-driver:src/arbol_codex_driver/identity.py#lifetime_matches
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.observe
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.settle_identity
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.require_remove_receipt
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.merge
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.store_run_usage
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.reserve
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.finish
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.reap
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.set_tool
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.stop_pending
arbol-codex-driver:src/arbol_codex_driver/run.py#run
arbol-codex-driver:src/arbol_codex_driver/runs.py#same_reservation
arbol-codex-driver:src/arbol_codex_driver/runs.py#Runs.reserve
arbol-codex-driver:src/arbol_codex_driver/runs.py#Runs.recover
arbol-codex-driver:src/arbol_codex_driver/runs.py#Runs.update
arbol-codex-driver:src/arbol_codex_driver/runs.py#Runs.finish
arbol-codex-driver:src/arbol_codex_driver/continuity.py#Chats.select
arbol-codex-driver:src/arbol_codex_driver/continuity.py#Chats.settle
arbol-codex-driver:src/arbol_codex_driver/continuity.py#Chats.matches
arbol-codex-driver:src/arbol_codex_driver/arguments.py#parse_arguments
arbol-codex-driver:src/arbol_codex_driver/arguments.py#validate_identity_arguments
arbol-codex-driver:src/arbol_codex_driver/subscriptions.py#Subscriptions.identity
arbol-codex-driver:src/arbol_codex_driver/state.py#State.initialize
arbol-codex-driver:bin/entry.py#bootstrap
-->

#### Requirements

| ID | Requirement | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-1.17 | implement revision-1 local capture/compare and format-2 lifetime evidence with the Driver-specific rules above; preserve ordinary catalogue/auth/refusal behavior | DRV-0.17, DRV-1.28–1.30, DRV-6.17–6.20 | BRW-D32 | pending ABR-38; application ABR-19/21 |



### ABR-40 concrete writer and maintenance refinement

Implement the exact shared DRV-6 cooperative custody, immutable payload/capability/acceptance validation and fixed administrative argv/context/result protocol. Every Driver metadata writer and detached helper independently opens shared component admission before first state access; durable preregistration and acknowledged child handoff precede parent release. Delayed writes remain bound to captured lifetime, and no helper writes after lease release. Lost handoff/custody stays refused pending exact cooperative evidence or the durably closed boot recovery; neither main exit nor group emptiness is proof. Existing vendor ownership/cleanup requirements remain separately intact. Legacy execution is tainted by the shared provider before execution; this producer does not install gates or trigger a reboot. All four exact state upgrade/identity-reset/restore/identity-recover commands consume the same context and idempotent attempt/generation protocol, preserving metadata-only archives and native credential boundaries. Source packaging declares exact M/D bytes, not qualified acceptance. ABR-38 owns actual five-repository qualification and genuine boot-transition evidence.

ABR-34 waits for ABR-40 **and ABR-41**. Current source CLI dispatch at `cli.py#main` calls unrestricted `Subscriptions.create`, `sign_out` and `remove`; `Subscriptions.start` passes `self.file(id_, "home")`, ordinary `run.py#run` passes `subscriptions.file(request.subscription_id, "home")`, and `AppServer.start` calls `write_driver_config` and `clean_environment(..., str(home))`. That production source path conflicts with existing CDX-1.2/.5/.6 and CDX-2.1/.2; it says nothing about installed behavior. ABR-41 separately repairs native-home/config/refusal compatibility. ABR-34 rereads its immutable hand-over before writer coverage/planning; no vendor transport repair is hidden inside identity. Preserve private historical homes/records; they do not become authorized real qualification profiles.

Writer inventory for ABR-34 includes State initialization/atomic deletion, Subscription reserve/finish/reap/set_tool/merge, usage/run_report, Runs recovery and Chats settlement plus ordinary CLI/error/final cleanup. Map every actual helper spawn to custody or an explicit no-Driver-metadata-write disposition. ABR-41's native subprocess remains under its existing vendor cleanup contract; any Driver-owned watcher that writes metadata participates in this protocol.

ABR-40 actual-review correction: consume DRV-6's exact `-ISB` bootstrap/D.importRoots and normal/helper `ARBOL_DRIVER_ADMISSION_FD`/`ARBOL_DRIVER_ADMISSION_CONTEXT` wire. Validate registry/boot/epoch/own and parent process identity, exact payload/entry/acceptance and the offer/ready/go/started acknowledged handoff before any Driver state access. Each child opens its own independent lease; no inherited main lock or exclusive-maintenance receipt substitutes. Source/helper declarations and candidate state never become qualified Browser authority.


### ABR-34 static foundation checkpoint · 14 November 2026

Published source `841c86b61c52aafc525c2721cf44cbe257436275` supplies only the first three accepted producer-plan leaves: bounded canonical identity values/private descriptor-relative durable file primitives, complete immutable M/D payload verification, and explicit registry gate/platform/scoped acceptance verification. These modules remain unconnected to CLI/state dispatch. They do not emit a Subscription proof, capability, acceptance, maintenance receipt or runtime qualification. Admission/bootstrap, lifetime/format/writer/offline operations and packaging remain future source work. Ruff, strict source-scoped mypy and source AST/diff checks passed without importing or executing the product; tests, providers, native profiles/credentials, normal Builds, gates, state conversion, installation and boot were not run. CDX-1.17 remains accepted/pending qualification; Source Refs above identify this partial foundation only. Indexed Mycel Origin/retrieval verification remains unavailable and no ingest/embedding occurred.


### ABR-34 admission source checkpoint · 15 November 2026

Published source `36afc09b7c13e069993e5bf823eb646843f95fe4` completes only accepted plan leaves1–8. The later batch adds the exact Darwin kernel-microsecond process identity, confined -ISB/bootstrap/import roots, exact normal main/helper offer/ready/go/started admission, independent writer leases, preregistered same-invocation helper API and durable terminal/unknown-custody settlement. Admission timestamps are UTC with six integer-preserved microsecond digits; historical Driver-state/native cleanup owner records are unchanged. Context is opened only after the postspawn offer, matching the provider's publication order. The helper API tracks in-flight spawning threads and retains admission if their final protocol effects remain uncertain. The existing excluded shell launcher was published through Forester's documented exact --skip-path reason; its -ISB change remains tracked and booked, without pretending that Mycel includes the excluded file.

These are static source contributions, not an executable producer/qualification pass. Bootstrap now requires immutable payload metadata and live normal/maintenance authority; packaging and maintenance implementation remain incomplete, so direct new source invocation refuses and no source bypass is supplied. Leaf9 still owns moving the ordinary run shell startup-ledger write into its admitted parent; lifetime/format/administrative/CLI/capability/packaging integration and ABR-38 runner wiring remain future work. No Subscription proof, qualified acceptance, usable maintenance or positive Browser binding is claimed. Five explicit Python inputs pass source-scoped Ruff/strict mypy and AST-only parsing; shell syntax and whitespace checks pass. No product/kernel adapter/helper/vendor/API/provider/profile/credential execution, tests/runners/gates, migration, Build/package, installation, boot or indexing occurred. The final independent actual-source review and all ABR-38 runtime gates remain required; CDX-1.17 stays accepted/pending qualification.


### ABR-34 startup and exclusive-authority checkpoint · 15 November 2026

Published source `d8d6aac2fb578c489a472d9ba8b72e55d00908f9` completes only accepted plan leaves1–10. The ordinary production startup shell no longer writes Driver metadata: the admitted parent durably publishes the same PID/lstart tool-owner.txt evidence and on_spawn run record, rechecks the blocked child's exact kernel identity and releases a private notification pipe only afterwards. The shell reads that pipe, closes its descriptor and execs the same native argv. EOF/cancellation/publication failure does not permit vendor exec; existing bounded process cleanup and the old orphan-ledger reader remain unchanged. Native HOME/configuration/options/refusals are preserved. This supersedes the earlier dated checkpoint's statement that leaf9's writer was pending; no runtime proof is added.

The exclusive maintenance validator consumes only the exact registered entry, administrative argv/context/receipt/pending-operation/qualified M/D/gate/platform tuple, agreed session paths and live inherited exclusive descriptor. It reasserts exclusive flock on that open-file description and requires an independently opened descriptor to remain blocked; it never LOCK_UNs the parent's copy. Paths are canonical/private and archives remain outside state/registry. It neither reads target payload contents nor converts/repairs state, drains custody, writes result receipts or opens admission. Actual format2/state/lifetime/administrative dispatch and packaging remain future leaves11–34, so no usable maintenance, identity proof/capability, qualified acceptance or Browser binding is claimed.

Source-scoped Ruff/strict mypy and AST parsing pass for app_server.py, run.py and maintenance.py. The generated notification-shell text passed syntax-only `/bin/sh -n -c` through AST literal extraction, without importing the product or executing that script/vendor. No tests, fixtures, runners, inventories, gates, product/native/provider/profile/credential/model/API execution, migration, package/Build, installation, boot, indexing, ingest or embedding occurred. Final independent actual-source review and ABR-38 runtime/gate qualification remain required. The unrelated CDX-2 working hunk and historical state/owner semantics were preserved.


### ABR-34 local state-admission checkpoint · 15 November 2026

Published source `de262af2faecb7590383ed5ed17fc722cdc656ec` completes accepted leaf 11, with managed Justifications `75817f5`. State initialization retains an independently opened close-on-exec shared `identity.guard` through state effects and output, with no destructor that releases it on object collection. Higher-format preflight is read-only; format/root generation are rechecked under the guard. Fresh qualified state publishes the format-2 fence and durable random root without materializing Subscription witnesses. Existing format 1 keeps legacy record behavior without automatic conversion or proof. Existing format 2 cannot recreate its missing guard or root; changed generation, unsafe state and local upgrade/maintenance markers refuse. No guard inode is replaced or unlinked.

The new internal `State.assert_admitted()` returns the captured `IdentityState`; `State.close()` is available for explicit settled final-output integration in leaf 26. Until then the process retains its independently opened guard through exit, even if the local State object leaves scope. Proof capture, record/lifetime journals, administrative state effects, CLI/capability and package metadata remain later leaves; this is not a complete usable producer. All 37 Python source modules pass strict non-incremental mypy and AST parsing, and the two changed files pass Ruff/diff checks without importing the product. No tests, native/helper/kernel/API/provider/profile/credential execution, state creation/conversion, Build/gate, installation, boot or indexed retrieval was performed. ABR-38 and final independent actual-source/Arc review remain pending.


### ABR-34 local proof checkpoint · 15 November 2026

Published source `fe6e88f123c71b4822ea3960976a9ef37b413368` completes accepted leaf 12, with managed Justifications `4f9a6d7`. The internal `Subscriptions.identity` path validates the mandatory exact safe selector and canonical expected pair, refuses format 1 with the specified upgrade remedy, and uses the existing canonical short lock. It validates only the local current record or implicit `chatgpt`; it never calls get/reap, settings-dependent authentication, app-server, vendor discovery or an application database. Under the same lock it refuses a pending journal, validates the strict sidecar, durably materializes a fresh independent witness when needed, compares captured generation/witness and returns only the bounded proof. A newly materialized witness cannot acknowledge an old expectation. Ordinary list, native account behavior, public record shape and application UUID authority are unchanged.

This is a source contribution, with no executed proof/capability or usable producer claim. CLI grammar/dispatch/capability and create/remove/lifetime/admin/packaging integration remain later leaves. Ruff on both changed files, strict non-incremental mypy and AST parsing over all 37 production Python modules, plus diff checks pass. No product, native/helper/kernel/API/provider/profile/credential/model, test/gate/Build, state creation/conversion, installation or boot execution occurred. Full independent actual-source review and ABR-38 qualification remain pending.


### ABR-34 bounded reader checkpoint · 15 November 2026

Published source `28558413df390d385904a44d31074e55f0310105`, with managed Justifications `ab22c32`, adds O_NONBLOCK to the existing descriptor-relative private protocol reader. It can reach its regular-file check without waiting for a FIFO writer; no-follow, ownership/mode, inode, size/stability and durable publication checks remain unchanged. This narrow static correction is new implementation leaf 13 after an independently accepted plan amendment; the current plan has 35 leaves and 13 completed. Ruff, strict non-incremental mypy over all 37 production modules and diff checks pass. No FIFO was created, and no product/helper/native/API/test/gate/owner-state action was executed; ABR-38 still owns runtime refusal and preservation evidence. Journal continuation is now leaf 14; no public proof CLI/capability or complete producer claim is added.


### ABR-34 journal source checkpoint · 15 November 2026

Published source `bcb6d733fc4fc68883e17c7477191a4e3359cc1c` adds the exact four-field pending create/remove journal and short-lock settlement helper. Prepared remove remains unavailable without the original operation's proven cleanup; missing progress, process death or record absence is no success evidence. Only a validated committed outcome can settle automatically. Retirement/record deletion, committed phase and pending-marker removal use durable private publication/deletion. Prepared create can retain that exact witness for a valid new record or retire it; a retired/different witness is not silently reactivated or transplanted. The original live remove may cancel its prepared marker only before any cleanup effect, preserving active proof. The helper refuses canonical native chatgpt removal and introduces no public creation route or new record field. Its caller must validate any current record and original owner/attempt evidence while holding the canonical short lock; removal integration remains future work.

One-file Ruff, strict non-incremental mypy over all37 production source modules, AST parsing of all37 without product imports and diff checks pass. No tests/fixtures/runners/inventories/gates, special-file/FIFO creation, product/native/kernel/helper/API/provider/profile/credential/model/state execution, Build/package/install, boot, indexing, ingest or embedding occurred. A separate static finding in the old state.read_json(Path.read_text) reader is allocated to a new source leaf awaiting independent cold review before any edit or removal integration; the journal helper does not rewrite completed reader/source checkpoints or invent a legacy-record size limit. Source remains incomplete and unqualified; independent actual-source review and all ABR-38 qualification remain required.


### ABR-34 legacy reader checkpoint · 15 November 2026

Published source `eaa6283e90dbd005e4513548b71f71e17553d0ea`, with managed Justifications `c5237ae`, repairs the existing record/progress/run JSON reader. It opens without following a final symlink and without blocking on a special file, validates a regular-file descriptor before reading, and closes the descriptor on every path. Existing text decoding, JSON grammar, record sizes and missing/null/malformed outcomes remain; no canonical-JSON or 4096-byte legacy-record cap was added. This is accepted new leaf 15 of the 36-leaf plan, after the journal contribution in leaf 14. Source-only Ruff, strict non-incremental mypy over 37 modules and diff checks pass. No FIFO, product/test/runtime or owner-state action ran; full independent source review and ABR-38 evidence remain pending.


### ABR-34 lifetime-writer and grammar checkpoint · 15 November 2026

Published source `050fbc013cab40f8fa0ed0ff4c544a8ffc4192cb` completes accepted leaves16–20; current progress is20/36. Historical removal now binds its original owner/attempt and captured witness to durable prepared/committed settlement. Permitted home/chat cleanup runs outside the short lock and deletion errors preserve ambiguity; process death, missing progress or absent records never prove cleanup. The canonical native chatgpt refusal remains before effects. Relabeling and auth metadata preserve existing proof; native HOME/configuration/account-read/cancel-without-logout and historical Owner semantics are unchanged.

`LifetimeSnapshot` is an internal immutable subscription/generation/witness tuple, captured with the validated local record under the short lock. Delayed check/usage/model/auth-verdict/run-derived updates compare it before record mutation, retaining the old auth revision checks. Private sign-in progress and run/chat metadata store the strict tuple as `lifetime`; no field is added to parse_record or the public catalogue. Progress reserve/finish/set_tool/stop_pending/reap compare owner/attempt plus that captured evidence; missing format2 evidence is unavailable, never inferred from current proof. Reap can preserve existing process cleanup but cannot erase a pending journal or mutate a newer lifetime. The original live remove may commit only its own prepared witness and receipt.

Run reservation, later reports and Chats settlement carry the same captured tuple. Format2 maps additionally receive an independent random private `revision`; optimistic publication compares the captured map, and failed/orphaned run deletion requires the exact captured revision and lifetime. A later same-conversation map cannot be erased from a matching conversation id alone. Missing legacy map/run lifetime evidence is not promoted to format2 authority; format1 reads/writes retain their legacy route. Exact reservation metadata and orphan process cleanup remain available after Subscription retirement, while delayed Subscription/map effects are fenced. Public run-list fields and native thread-resume transport remain unchanged.

The parser now recognizes the exact identity/expect and state upgrade/identity-reset/restore/identity-recover families, rejects duplicate/unknown/inapplicable arguments, requires each fixed flag/value and absolute canonical administrative paths, and treats quiescence solely as an assertion. This is grammar only: early CLI dispatch/settled State.close is leaf28, administrative archive/marker/conversion/reset/restore/recovery effects start at21, and capability/immutable packaging remain later work. No new executable producer, proof/capability/acceptance or maintenance success is claimed.

Ruff passes over the authored six files; strict non-incremental mypy passes over37 production source modules, and AST parsing passes those37 plus bin/entry.py without product imports. Diff checks pass. No tests/fixtures/runners/inventories/gates, product/native/kernel/helper/API/provider/profile/credential/model execution, state creation/conversion, Build/package/install, boot, indexing, ingest or embedding occurred. Full indexed Origin/retrieval verification remains previously unavailable; deterministic local plan/paths/direct-Origin and Source Ref checks are recorded in the Beat. Source and managed Justifications are pushed; unrelated CDX-2 bytes are preserved. Shared DRV references remain coordinated separately. Final independent actual-source review and all ABR-38 runtime/gate qualification are still required.


### ABR-34 immutable metadata archive checkpoint ·15 November2026

Published source `e41d58b94b1e1f9cddc8f9b10b4df2a5e752a12e` adds metadata-only immutable archives with canonical bounded manifests, lexical paired presence/absence, exact raw before-image hashes, strict valid-source checks and same-attempt private preservation binding. Source-only Subscription directories may be genuinely absent from current state; the reader walks no-follow parent descriptors and treats only ENOENT as absence, while unsafe existing paths refuse. It creates no ordinary Subscription/record while taking a snapshot. Malformed bounded failed bytes are preserved as evidence but a null-format archive cannot authorize restoration. Records/auth/native homes/chat/live guard/registry authority remain outside the metadata allowlist.

Interrupted private writer staging is retained outside the immutable entry, and complete entries are verified rather than rewritten. This completes source leaf21 only: local operation markers/results, conversion/reset/recovery/restore and early CLI integration remain subsequent work. Ruff, AST, strict no-incremental mypy over38 production modules and committed-file whitespace checks pass. No archive function, product/helper/native/API/profile/model/provider/credential/state operation, test/fixture/runner/inventory, Build/gate/package/install or boot was executed. Full independent source review and ABR-38 qualification remain pending.

<!-- sources:
arbol-codex-driver:src/arbol_codex_driver/identity_backup.py#Archive
arbol-codex-driver:src/arbol_codex_driver/identity_backup.py#metadata_names
arbol-codex-driver:src/arbol_codex_driver/identity_backup.py#read_bytes
arbol-codex-driver:src/arbol_codex_driver/identity_backup.py#preserve
arbol-codex-driver:src/arbol_codex_driver/identity_backup.py#preserve_entry
-->


### ABR-34 local maintenance checkpoint ·15 November2026

Accepted leaf22 is published as source `37b7bf097988ac4bd222c3944c5d26c69ebf9b04`, managed Justifications `d18d484a96c92822214cb5527be24e9f6d9fd31e`. `Operation` consumes only this invocation's entered/rechecked maintenance handoff before target preflight, independently opens/retains exclusive stable identity.guard, and never unlocks/replaces it. Format1 may establish the missing pre-identity guard only under the verified drained component fence; existing format2 cannot recreate a missing guard. Local pending/complete markers bind exact context generation/attempt/source/before-manifest hashes. Mismatched reuse refuses. Completion reconstructs the exact bounded child maintenance tuple only from format2/exact root, immutable same-attempt archive, matching local marker and operation-relative cleared journals. Targeted recovery preserves unrelated well-formed pending journals and their per-selector refusals; malformed metadata refuses closed. The provider alone publishes result.json, archives the complete marker and reopens admission.

The module supplies checkpoints, not conversion/reset/restore/retire algorithms or CLI wiring. Two-file Ruff, strict non-incremental mypy over39 production modules, AST parsing those39 plus bin/entry.py without product imports and diff checks pass. Source and managed Justifications are pushed. No tests/fixtures/runners/inventories/gates, product/archive/helper/native/kernel/API/provider/profile/credential/model/state operation, Build/package/install, boot or separate indexing/ingest/embedding command ran. Final independent full-source review and ABR-38 remain required; no maintenance/runtime success is claimed.

A subsequent static composition audit found that ordinary reap currently requires a dead progress receipt's former lifetime to match active current proof. Supported reset/restore changes generation, and targeted retirement changes witness, while preserving that progress; reserve can then refuse forever. No reproduction was run. The existing current-record/dead-owner rule in DRV-6 and captured-lifetime discard rule require separating fresh exact orphan-progress cleanup from authority of an old result. The Beat now proposes a narrow new unticked leaf23 for independent cold review before source changes. Former unticked algorithms23–36 become24–37. Completed source1–22 stays intact; no new progress/auth schema, native policy, positive proof or cross-lifetime verdict is accepted by that draft. Unrelated CDX-2 bytes remain untouched.


### ABR-34 recovery and offline-algorithm checkpoint ·15 November2026

Published source `1b3a23c2ac5dc9b60244d5566d8a71a0f07ea4fa` completes accepted leaves23–28, current28/37. Fresh ordinary reaping now captures the full unchanged dead progress receipt plus validated current record/root/strict sidecar observation under the short lock, retains original process cleanup outside it, then deletes only that same receipt durably after unchanged/dead rechecks. It writes no verdict, witness or pending journal and retains settled signed-in records/successor progress. Stale merge refuses before get/reap. Format1/native cleanup behavior and all original delayed lifetime/attempt/auth checks remain.

Exclusive algorithms now use the context's selected generation throughout immutable before-manifests, local markers, upgrade journals and retry results. Upgrade stages/fsyncs the root, publishes format2 before root proof and clears its exact journal last; repeated valid-format2 upgrade keeps its generation. Reset rotates only root identity, leaving witnesses/records/native/auth unchanged. Conservative recover retires only its archived pending witness under the canonical short lock, leaves records/credentials/progress as found, clears only target pending and preserves unrelated well-formed pending journals. The normal post-maintenance reaper can then dispose of the exact old dead progress without adopting an old result.

Restore verifies source/hash and private metadata-only source/current union before replacements, preserves raw failed metadata and historical journals, binds durable restore intent and leaves live guards/registry/native state untouched. Only an actually empty canonical target may establish a new guard under exclusive restore authority; existing format2/unsafe state cannot recreate one. Declared absence removes identity metadata only. Historical journals remain read-only evidence, never current authority. Interrupted conversion-before publication can resume; once its format2 fence is crossed the same attempt resumes conversion without reapplying format1. Format1 internally reconverts through its own conversion-before/manifest.json and exact fresh context generation; format2 settles the same fresh generation. Source Subscription pending transactions are refused before restore mutation rather than fabricated cleanup; use a clean verified metadata source or the explicit conservative route. Exact local completion/result checks and provider-only result/reopen duties remain unchanged.

All39 production modules pass strict non-incremental mypy; AST parsing passes those39 plus bin/entry.py without product imports; authored targets pass Ruff and diff checks. No tests/fixtures/runners/inventories/gates, product/archive/native/kernel/helper/API/provider/profile/credential/model/state operation, Build/package/install or boot ran; no separate indexing/ingest/embedding command was invoked. CLI dispatch/capability and immutable packaging remain leaves29 onward, so no executable maintenance/proof/qualified acceptance/Browser pass is claimed. Source/managed Justifications are pushed, Source Refs identify static contributions only, and unrelated CDX-2 bytes remain preserved. Final full-source independent review and ABR-38 remain pending.


### ABR-34 CLI and package-source checkpoint ·15 November2026

Published source `16b3e9611463632577b655250e02819dc57d082a` completes accepted29–32, current32/38 after the proposed reader amendment below. CLI requires actual normal admission even for format1/source execution, dispatches local identity before settings contents/run reaping/get/native discovery, and dispatches only the exact entered maintenance request before normal State initialization. Identity emits only its proof/refusal with no account notices. Info adds subscriptionIdentity1 from the exact verified declaration without another tool check; ordinary fields/tool discovery remain. Immutable pyproject version plus registered D Build supply normal reporting. Synchronous Invocation owns normal State/exclusive Operation through final output, error cleanup and asyncio.run task/executor joins; only then does it explicitly close, while outer component admission remains held.

Package source now stages exact clean committed Git-archive input and the original pinned standalone runtime inside fixed driver-payload. It emits complete lexical M over runtime/libraries/bootstrap/source/scripts/tests/provenance and declared links, excluding only root M/D; exact D binds registered Build, clean commit/tree, regular pinned interpreter/bin entry, fixed helpers/import roots and integer capabilities. It checks normalized collisions, special/external/dangling/cyclic links and changed bytes. Existing root entry/runtime/scripts/test/package paths are links into those same immutable bytes, and wrapper execution uses -ISB. Mutable registered Build metadata/log/last-start stay outside M. Source/static unregistered candidates receive no D or acceptance; no build0 identity authority is fabricated. Existing package provenance omits only its own record and the two exact generated M/D names in addition to its historical runtime-hash disposition; complete M independently includes the runtime. Build metadata changes only dataFormat1→2; entry, version and every gate command string remain identical.

Ruff/strict source-scoped non-incremental mypy/AST checks pass for the CLI/build/entry and three package sources; generated shell text passes syntax-only sh -n via AST extraction, without running it. The cached public arm64 archive headers show python/bin/python3.14 is regular and stdlib/lib-dynload directory prefixes exist; directory entries themselves are implicit. No archive extraction, pinned-runtime or package-function execution occurred. No tests/runners/gates, product/native/kernel/helper/API/provider/profile/credential/model/state action, Build/install/boot or separate indexing/ingest/embedding command ran. The tracked arbol-build.json is excluded by Mycel source chunks and was normally managed-published with an exact --skip-path reason; no indexed code coverage is invented for it. Full-source/static-input review and all ABR-38 qualification remain pending; current README/candidate leaves are unfinished.

A subsequent static audit found two remaining legacy text opens: state.read_lock uses Path.open before fstat/type validation, and Runs.orphan_groups uses Path.read_text for tool-owner.txt. They can block on a FIFO before detecting unsafe input, unlike the completed PrivateDirectory/read_json repairs. No FIFO was created or source probe run. A new unticked33 proposes only nonblocking/no-follow regular descriptor validation/exception-safe closure for those two readers, preserving valid decoding/grammar/error/size/owner semantics. It awaits fresh independent cold review before source changes; future docs/static-input steps are renumbered only. All completed1–32 source/text and unrelated CDX-2 bytes remain preserved.


### ABR-34 reader/documentation checkpoint ·15 November2026

Accepted reader33 is published as source `75f9329c6a1e6d82e58587d7945199d1c4ccaf5e`, managed Justifications `e09bb10887adac6414f069de41eb3460ae3ddc9f`, after independent changed-plan acceptance `965ceb9`/wording record `e07fe8a`. read_lock and only orphan_groups's fallback tool-owner.txt now independently open no-follow/nonblocking/close-on-exec descriptors, validate regular-file type before text and close even if wrapping/reading fails. read_lock retains its original descriptor stat snapshot and existing JSON/owner/error rules. The ledger retains default text decoding/newlines, strip/splitlines, two-line decimal-PID/lstart parsing, missing-file fallback and explicit run-record-tool precedence. No legacy size cap, owner tolerance, reclamation/signal policy or proof schema changes. No FIFO or behavioral probe ran.

Documentation34 is published through source `983b8fbd71f709e826fa5188ed1ef529fd0743b2`, Justifications `19c7521d48cad8aa425bb44298d3d463ee7c1e03`, retaining its initial `93385af`/`4700306` publication. README now states the exact admitted identity/format1/offline maintenance/metadata archive/immutable payload boundaries, retains native compatibility and historical text under explicit history headings, and makes static inputs/unfinished qualification distinct from usable installed or Browser authority. No README/current gate command or test source was executed. All authored code leaves have normal managed Justifications; excluded tracked Build metadata32 retains its documented exact skip reason. Shared DRV Source Refs remain coordinated with the root and no normative row/status was changed here.

The complete source through34 is clean and pushed. Test-free source Ruff/strict non-incremental mypy/AST/diff checks pass for the reader repair and earlier authored inputs. Full final static checks/immutable source-input freeze and a fresh independent whole-source verdict remain following leaves35–37; final38 stays incomplete until that review. No tests/fixtures/runners/inventories/gates, product/helper/native/kernel/API/provider/profile/credential/model/state operation, packaging/generator/runtime function, Build/install/boot or separate indexing/ingest/embedding command ran. The shared provider snapshot remains unfinished/unqualified while its signal-mask repair is pending; no actual registered five-repository/runtime/M-D/gate/acceptance tuple is fabricated or inferred from these refs. Unrelated CDX-2 bytes remain untouched and all ABR-38 runtime/gate/boot obligations remain.


### ABR-34 implementation reference boundary ·15 November2026

Leaf35 integration binds clean source `983b8fbd71f709e826fa5188ed1ef529fd0743b2`, tree `d81a4b80704f4c92748684f30a480962ae854047`. Every authored source leaf through34 has its normal managed Justifications, including documented exact reasons for excluded tracked metadata/shell paths. All83 Codex Source Refs resolve directly to current files/AST symbols; the public record whitelist and proof schema remain unchanged. The coordinator published implementation-only DRV-0/1/6 appendices at `2d93a4d01552fd2a56d5becdbecc6447bcd87632`, corrected the Runs.orphan_groups anchor at `2b3e679`, and released the shared window. Current shared corpus `4755146828437f10e397c2c95dbe480ccc0e8037` additionally records provider source progress without normative/status changes. It is the contract snapshot for the frozen input boundary; unrelated owner working/index hunks were preserved rather than incorporated here.

Required shared provider source is currently `933e82ba7f9e41b1dff1f0cc7cbb05cd543b304f`, tree `81c65e4b169a8189f8b43c13c3a60f43186a0405`, with fresh source review pending. It is an unfinished/unqualified interface snapshot, not an accepted executable tuple. Registered producer/provider Builds, complete executable runtime roots, actual M/D, launcher/gate/acceptance and five-repository qualification remain unproduced for this source checkpoint. Final immutable input freeze and fresh independent whole-source review still precede leaf38 completion, and every ABR-38 runtime/native/recovery/gate/boot obligation remains. No ingest/embedding or indexed verification is implied by local Source Ref integration; indexed availability remains a separate previously unavailable check.


### ABR-34 final source acceptance and qualification hand-over ·15 November2026

The fresh independent whole-source/static-input reviewer delivered **accepted with no verified consequential findings**, recorded by the coordinator at Forester `9d29a0471317c8c35f1f100fae8ee3342c8316e5`. Exact source remains `983b8fbd71f709e826fa5188ed1ef529fd0743b2`, tree `d81a4b80704f4c92748684f30a480962ae854047`; no source change or version bump follows from final publication. The frozen `/Users/msix/.local/state/arbol-browser/abr34/source-checkpoint-983b8fbd-44b2422/` remains byte-identical: artifact manifest `f7840b12b6074aa8a9410b6c3afab2ce3f9642f0d3aa582ab5dcfdeaa2887a1a`, review-input `019976e842e0f0b99e5844d4eb93c142d89d76f923c1c54ef2c54fee466ed8f3`. The manifest declares43 files and excludes itself, yielding44 readonly files total. All110 source blobs/modes,24 authored copies,104 package inputs and committed corpus snapshots were independently verified. Existing managed Justifications and Source Refs remain; no normative requirement/status row is changed.

Numeric info/build metadata contract1 intentionally remains the accepted baseline of leaves29/32. Shared Contract2 wording is a retained compatibility discrepancy: **ABR-38 must explicitly reconcile it before qualification**, including the five-repository/consumer composition. This source verdict does not certify Contract2 compliance. Subscription identity capability1 and payload contract DRV-browser-identity-1 are distinct from the numeric field. No concrete new identity-path failure or authorized version change was found. Keep this issue in the exact qualified tuple/evidence and future Backend composition hand-over, not an inferred source fix.

ABR-34's implementation-only source scope is complete upon its final leaf38 publication. All registered producer/provider Builds, expanded executable runtime roots, actual M/D, launcher/gate/acceptance, runtime/full-gate qualification and genuine-boot/deployment tuples remain unproduced for this checkpoint. The copied public runtime archive/member hashes are static input bytes only. ABR-38 owns retained dev/archived runner admission wiring, all five complete ordinary gates, old/new format/proof/race/late-result/process/import/helper/custody/native/maintenance/archive/crash/retry/restore/retire/result/reopen cases, compatibility reconciliation and a separately scoped genuine-transition proposal/evidence. Final independent Arc Review and every consumer prerequisite remain intact. No product/package/generator/runtime/test/gate/owner-state action, index ingest or embedding ran during final publication. Unrelated CDX-2 bytes and all old checkpoints/candidates remain unchanged.


### ABR-45 nested admission and helper declaration source · 15 November 2026

Source `74a13d7772f4fdc56799cd1258a607df7865a2ba`, tree `37f003007efa9d729ace8ecee13e67625983bde2`, exposes the existing one-use helper handoff as prepare_helper and uses it for both synchronous and asynchronous spawning. The ticket retains its parent spawn obligation through acknowledgement, joins acknowledgement work before closing its owned socket, and forwards only its existing handshake descriptor. Both shipped execute_run bodies now independently admit the nested public bin/entry.py process while retaining request/control streams, environment, native HOME/config/auth and bounded cancellation cleanup. The archived body is shipped production orchestration; actual test methods and fixtures are unchanged.

Immutable package declarations add only scripts/check_build.py and the reserved tests/identity_actor.py beside the public entry, requiring regular inventoried bytes. Missing future bodies refuse packaging; a filename is no actor-body admission. Numeric contract1 remains distinct from subscription identity capability1 and payload DRV-browser-identity-1. Managed per-leaf Justifications are published. This is implementation/source evidence only: complete gates, future runner/actor bodies, actual M/D/Build/acceptance and runtime qualification remain ABR-38. No product/package/generator/test/native execution or separate index ingest/embedding ran.

<!-- sources:
arbol-codex-driver:src/arbol_codex_driver/admission.py#Session.prepare_helper
arbol-codex-driver:src/arbol_codex_driver/admission.py#Session.spawn_helper
arbol-codex-driver:src/arbol_codex_driver/admission.py#Session.spawn_helper_async
arbol-codex-driver:src/arbol_codex_driver/admission.py#HelperHandoff
arbol-codex-driver:src/arbol_codex_driver/dev.py#execute_run
arbol-codex-driver:tests/mid/archived/src/arbol_codex_driver/dev.py#execute_run
arbol-codex-driver:scripts/identity_package.py#emit
-->
