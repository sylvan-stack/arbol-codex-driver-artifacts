---
role: authored
---
# Probe: does a Codex rate-limit window say what it counts? · 26 October 2026

The research record behind CDX-1.16 and CDX-D31 (SYL-292): whether the app server's usage answer names the unit of a window, so that the Driver could fill the contract's `resource` field (DRV-1.27, DRV-D46) without guessing.

## What was probed

`codex app-server generate-json-schema --out <folder>` of the installed `codex-cli` 0.162.1, on 26 October 2026 at 22:50 UTC, from a clean login shell, with `CODEX_HOME` pointing at a disposable empty folder. No prompt was sent and no account was read; the command writes the protocol's JSON Schema and nothing else. The generated schema stays outside Git in `~/Library/Logs/Arbol/codex-app-server-schema-0.162.1-2026-10-26/`.

## What the schema says

| Definition | Fields |
|---|---|
| `RateLimitWindow` | `usedPercent` (integer, required), `windowDurationMins` (integer or null), `resetsAt` (integer or null, seconds since 1970) |
| `RateLimitSnapshot` | `primary` and `secondary` (`RateLimitWindow` or null), `credits` (`CreditsSnapshot` or null), `individualLimit` (`SpendControlLimitSnapshot` or null), `limitId`, `limitName`, `normalModelSlug` (string or null), `planType`, `rateLimitReachedType` (`rate_limit_reached`, `workspace_owner_credits_depleted`, `workspace_member_credits_depleted`, `workspace_owner_usage_limit_reached`, `workspace_member_usage_limit_reached`), `spendControlReached` (boolean or null) |
| `CreditsSnapshot` | `balance` (string or null), `hasCredits`, `unlimited` (booleans) |
| `SpendControlLimitSnapshot` | `limit` and `used` (strings), `remainingPercent` (integer), `resetsAt` (integer) |
| `GetAccountRateLimitsResponse` | `accountId`, `ordinaryUsageAllowed`, `rateLimitResetCredits`, `rateLimitUpsell`, `rateLimits`, `rateLimitsByLimitId` |

No field of a window names what it counts. The descriptions speak of "usage" and "included usage" and never of tokens, messages or requests. `credits` is the account's credit balance that sits beside the windows, not a window's unit; `individualLimit` is a spend control with a currency-like `limit` and `used`. The real answers recorded on 7 October 2026 with `codex-cli` 0.159.2 (`research/run-2026-10-07.json`) have the same shape.

## Outcome

The vendor does not say what a Codex window counts, so the Driver leaves `resource` absent on every window rather than guess (DRV-1.27; CDX-1.16, CDX-D31). The credit balance stays in `extra.credits` as before. Should a later schema add a unit to `RateLimitWindow`, the mapping is revisited.

<!-- sources: arbol-codex-driver:src/arbol_codex_driver/catalog.py#normalize_window arbol-codex-driver:tests/test_foundation.py -->
