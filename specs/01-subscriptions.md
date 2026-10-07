---
role: authored
spec: CDX-1
status: accepted
---
# Codex Driver · 01 Subscriptions

How the Codex Driver meets [DRV-1](../../arbol/driver-contract/01-subscriptions.md) with the `codex` command-line tool. It serves one vendor family, ChatGPT accounts, and does all account work through the tool's app-server running in a home that belongs to one Subscription. It matters because version 1 had no account handling on this route at all: a turn ran as whoever was logged in to the tool on the machine, whatever Arbol showed.

## Scope

Covered: the `chatgpt` family, the home and environment each Subscription gives the tool, sign-in and sign-out, status checks, usage, the model catalog.

Not covered: the contract itself (DRV-1); threads, turns and the configuration a run starts the app-server with (CDX-2); approvals and sandbox settings (CDX-3); recognising a rate limit or a rejected login in the output of a run (CDX-4).

## Behaviour

### Family

| Family | Vendor | Sign-in | Settings |
|---|---|---|---|
| `chatgpt` | OpenAI | The vendor tool's own ChatGPT login | None |

Not offered in the first release: key-billed OpenAI accounts and the cloud-provider logins the tool's protocol also lists.

Observed in version 1: one built-in ChatGPT account. Two routes drew on it: the vendor tool route, and a direct client for the ChatGPT backend that is retired.

<!-- sources:
arbol:daemons/core/arbol_core/subscriptions.py#DEFAULT_SUBSCRIPTIONS
arbol:product-spec/05-intelligence-providers.md#Concept model
-->

### Home and environment

Every Subscription has a folder of its own in the Driver's state directory, created readable by the owner only. The Driver passes it to the tool as `CODEX_HOME` for every child process it starts for that Subscription. The tool keeps its login and its configuration there. The Driver writes the configuration in that folder itself and never reads the login the tool stores there.

The environment of a child process starts from an allow-list of inherited variables (home, path, user, locale, temporary directory, proxy and certificate settings). Nothing named `OPENAI_*` or `CODEX_*` is inherited. `CODEX_HOME` is then set to the Subscription's home.

When an app-server starts, its answer to the opening handshake names the home it uses. The Driver compares that with the Subscription's home and stops the process when they differ.

Observed in version 1: the tool route injected no credential and did not redirect the tool's home. A turn ran with the home the service inherited, normally the Leather Bag's own `~/.codex`, login and configuration included. Because that configuration was not Arbol's, a turn was refused when it contained settings Arbol could not represent. The account bound to the route served only to attribute usage and to select a model list.

<!-- sources:
arbol:product-spec/05-intelligence-providers.md#Account profiles for the Claude tool
arbol:product-spec/05-intelligence-providers.md#Can two accounts of one vendor run at the same time, isolated?
arbol:daemons/core/arbol_core/subscriptions.py#DEFAULT_IP_BINDINGS
arbol:drivers/codex/arbol_driver_codex/session.py#codex_home
arbol:drivers/codex/arbol_driver_codex/session.py#validate_config
-->

### Signing in and out

Proposed. The Driver starts an app-server in the Subscription's home and asks it to log in.

| Contract step | App-server exchange |
|---|---|
| Sign-in on this machine | Request `account/login/start` with type `chatgpt`. The answer carries an authorisation address and a login identifier; the Driver returns `open_url` with that address |
| Sign-in from another device | Request `account/login/start` with type `chatgptDeviceCode`. The answer carries a verification address and a user code; the Driver returns `open_url` with both |
| Completion | Notification `account/login/completed` with `success` true: the Driver reads the account and returns `done`. With `success` false: `failed`, carrying the tool's error text |
| Cancel, replacement, time-out | Request `account/login/cancel` with the login identifier, then the app-server is stopped |
| Sign-out | Request `account/logout` |

The app-server stays running while a sign-in is pending, because it is the tool that receives the vendor's callback. The Driver holds no ChatGPT credential and renews none; the tool does both.

Only one sign-in on this machine can be pending at a time, across all homes, because the tool receives the callback on one fixed local address. The Driver therefore lets one such sign-in be pending across all its Subscriptions, and reports a sign-in that another login on the machine has ended as `failed` with that reason. The device-code sign-in has no such limit.

Observed with the installed tool on 5 October 2026: the authorisation address is on `auth.openai.com` and the tool listens on `127.0.0.1:1455` while the sign-in is pending. The tool does not open a browser itself, so the caller's window can show the page. A second sign-in started in another home succeeded and ended the first with "Login cancelled". The device-code answer carries the address `https://auth.openai.com/codex/device` and a code of the form `XXXX-XXXXX`.

The existing login in the Leather Bag's own `~/.codex` is not taken over. A Subscription is signed in once, in its own home.

Observed in version 1: no in-app sign-in existed. The Leather Bag ran the tool's login in a terminal; "Check login" then copied the newest of two credential files from the home directory into Arbol's Keychain. The copy went stale as soon as the tool renewed its login, and Arbol's recovery was to copy again. Signing out in Arbol deleted the copy and left the tool logged in, so the route kept working.

<!-- sources:
arbol:daemons/core/arbol_core/universe_import.py#read_universe_auth
arbol:daemons/core/arbol_core/universe_import.py#import_from_auth_json
arbol:daemons/core/arbol_core/rpc/subscription.py#_login
arbol:daemons/core/arbol_core/orchestration/agent_attempt_execution.py#AgentAttemptExecutionService._refresh_bound_subscription_token
arbol:product-spec/05-intelligence-providers.md#Sign-in and sign-out
-->

### Status check

`check` starts an app-server in the home and sends `account/read` with `refreshToken` set, which makes the tool renew its login with the vendor before answering. An account of type `chatgpt` means `signed_in`; its e-mail address and plan are stored with the Subscription. No account means the login is gone: a Subscription that was `signed_in` moves to `needs_attention` with the remedy "sign in again". Any other account type in the home is reported as `needs_attention` as well, because this family only covers ChatGPT logins.

Observed with the installed tool: without `refreshToken` the request is answered at once from the home, without contacting the vendor; with it, the answer took about a second and the login file was rewritten.

Observed in version 1: the accounts page's Test passed for a ChatGPT route when the row said logged in, without contacting the vendor or the tool.

<!-- sources:
arbol:product-spec/05-intelligence-providers.md#Intelligence Provider settings
-->

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

<!-- sources:
arbol:daemons/core/arbol_core/universe_usage.py#normalize
arbol:daemons/core/arbol_core/universe_usage.py#build_headers
arbol:daemons/core/arbol_core/rpc/subscription.py#_codex_usage
-->

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

<!-- sources:
arbol:daemons/core/arbol_core/provider_models.py#fetch_codex_models
arbol:daemons/core/arbol_core/provider_models.py#installed_codex_client_version
arbol:daemons/core/arbol_core/provider_models.py#_arbol_is_special_purpose_codex_model
-->

## Requirements

| ID | The Codex Driver must… | Refines | Origin | Verified by |
|---|---|---|---|---|
| CDX-1.1 | offer the family `chatgpt` (vendor login, no settings), with one Subscription from the start, named `chatgpt`, which is the default | DRV-1.1 | Kept | `subscriptions.local`, `C1` (default account; default inference pending SYL-86) |
| CDX-1.2 | set `CODEX_HOME` to the Subscription's home for every child process of that Subscription, and create that home readable by the owner only | DRV-1.2 | Changed | `subscriptions.create`, `app-server.home`, `probe.subscriptions`, `live.subscriptions` |
| CDX-1.3 | stop an app-server whose handshake answer names another home than the Subscription's | DRV-1.2 | New | `app-server.validation` |
| CDX-1.4 | build each child's environment from an allow-list; no inherited `OPENAI_*` or `CODEX_*` variable reaches the tool | DRV-0.5 | Changed | `app-server.home`, `C8` (subscription children) |
| CDX-1.5 | write the configuration in a Subscription's home itself, and never copy the Leather Bag's own `~/.codex` or write to it. Read from it only what CDX-3.14 names | DRV-0.4 | Changed | `app-server.home`, `probe.subscriptions` |
| CDX-1.6 | sign in and out only through the app-server's `account/login/start`, `account/login/cancel` and `account/logout`, and hold no ChatGPT credential itself | DRV-1.8 | Changed | `C2`, `C5` (subscription scope), `probe.subscriptions`; successful browser consent recorded 6 October 2026, not repeated |
| CDX-1.7 | offer both the sign-in on this machine and the device-code sign-in, the second when `sign-in` is called with `--by-code` | DRV-1.5 | New | `C2`, `probe.subscriptions` (both sign-in methods return their steps; fresh browser consent not repeated) |
| CDX-1.8 | keep the app-server of a pending sign-in running until the tool reports completion, the attempt is cancelled or it times out, and leave no process behind afterwards | DRV-0.10 | New | `C2`, `C6`, `app-server.cancel`, `app-server.descendants`, `probe.subscriptions` |
| CDX-1.9 | never read, copy or log the login the tool stores in a home | DRV-1.3 | Changed | `app-server.home`, `subscriptions.snapshots`, `C7` (subscription scope) |
| CDX-1.10 | check a Subscription with `account/read` and a renewal of the login, and move it to `needs_attention` when the home holds no ChatGPT account | DRV-1.7 | Changed | `C4` (subscription scope), `app-server.rejection`, `live.subscriptions` |
| CDX-1.11 | build the usage report from `account/rateLimits/read` by the table above | DRV-1.17 | Changed | `catalog.usage`, `catalog.unknowns`, `catalog.malformed`, `C41`, `live.subscriptions` |
| CDX-1.12 | build the model catalog from `model/list`, all pages, without hidden models | DRV-1.20 | Changed | `catalog.models`, `catalog.pages`, `catalog.fallback`, `C41`, `live.subscriptions` |
| CDX-1.13 | make no request of its own to a ChatGPT or OpenAI address | DRV-1.19 | Changed | `app-server.home`, `C41` (only app-server account RPCs; no inference requests) |
| CDX-1.14 | let only one sign-in on this machine be pending across all its Subscriptions, and report a sign-in ended by another login on the machine as `failed` with that reason | DRV-1.5 | New | `C2` (cross-home local replacement and independent device codes), `probe.subscriptions` |
| CDX-1.15 | read a usage window's kind from its length | DRV-1.17 | New | `catalog.usage`, `catalog.unknowns`, `C41` |

## Verification on 7 October 2026

`test/probe-subscriptions.mjs` against installed `codex-cli` 0.159.2 sent no prompts. Its sanitized record is `research/subscriptions-2026-10-07.json` (`probe.subscriptions` and `live.subscriptions`). Fresh homes accepted the Driver configuration and reported it through `config/read`; both login methods returned their page addresses, and device sign-in returned a code. A second local login cancelled the first; cancellation and logout worked. The real app-server exited after its input pipe closed. On the existing signed-in `test-chatgpt` home, the Driver commands `check`, `usage` and `models` returned a signed-in account, an `ok` usage report and a tool catalog of seven models, including efforts and service tiers. No credential file was read or copied. New browser consent was not repeated, and the signed-in test account was not logged out. Browser completion remains the real observation of 6 October below.

`test/conformance-subscriptions.mjs` passes C1, C2, C6, C39 and C41 plus the subscription portions of C4, C5, C7, C8 and C40. Real run ownership, inference output and cancellation remain in SYL-86 and SYL-89; synthetic `subscriptions.active-run` tests exercise sign-out/removal against valid DRV-6 run records.

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

- **The route ran as the machine's login.** No credential was injected and the tool's home was not redirected. Two ChatGPT accounts could not run side by side, signing out in Arbol did not stop the route, and the usage shown could belong to another account than the one doing the work.
- **A rotating login was copied.** See DRV-1.
- **The vendor's backend was imitated.** Usage and model list were read from undocumented addresses with the tool's headers and a version number that had to be kept in step by hand.
- **The Leather Bag's configuration decided whether a turn could start.** A custom model provider, a saved permission or network profile and similar settings in `~/.codex` made Arbol refuse the turn.

<!-- sources:
arbol:product-spec/05-intelligence-providers.md#Can two accounts of one vendor run at the same time, isolated?
arbol:product-spec/05-intelligence-providers.md#Known problems and lessons
arbol:daemons/core/arbol_core/provider_models.py#_arbol_fetch_codex_models_payload
arbol:drivers/codex/arbol_driver_codex/session.py#validate_config
-->

## Decisions

| ID | Question | Proposed default | Outcome |
|---|---|---|---|
| CDX-D14 | How are account RPCs, sign-in races and configuration checked? | One JSONL app-server per operation, with a 30-second request bound, buffered login notifications and a process group of its own. Write the Driver configuration, verify it with config/read, and compare real home paths in initialize. Publish a sign-in reservation with an attempt token and by-code flag under the Subscription lock; a replacement sets stopReason before signalling. Local sign-ins in one state directory choose the latest process identity among simultaneous reservations; the vendor reports a local login ended from another state directory or program. Each network answer updates only the login state and checkedAt revision it originally checked. The five-minute sign-in bound covers startup, login and the final account read | Decided 7 October 2026 during SYL-81, a technical choice. No credentials are read by the Driver and no direct vendor HTTP client is used |
| CDX-D1 | Where does the tool keep a Subscription's login: its file in the home, or the system keychain? | The file, as the tool does by default: it is proven to be per home. The keychain would match the rule that secrets live only there, and is preferred once a probe shows it is also per home | Decided 6 October 2026, left to Claude by the owner: the file. `codex` keeps a Subscription's login in `auth.json` in its home, readable by the owner only, as it does for everyone who uses it. No move to the keychain is planned (SYL-35) |
| CDX-D2 | Should an existing login in `~/.codex` be taken over? | No. Copying it reproduces version 1's stale-copy defect; the Leather Bag signs in once per Subscription | Decided 6 October 2026 by the owner: the proposed default. A Subscription is signed in properly, which the Driver also needs to report the account's limits (SYL-63) |
| CDX-D3 | Which sign-in does the caller offer first? | The sign-in on this machine; the device code as the alternative, for a machine that cannot open the vendor's page | Decided 6 October 2026 by the owner: the proposed default (SYL-64) |
