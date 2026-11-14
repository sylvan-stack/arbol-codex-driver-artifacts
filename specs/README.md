---
role: authored
---
# Codex Driver specifications

How `arbol-codex-driver` meets the [Driver Contract](../../arbol/driver-contract/README.md) with the `codex` command-line tool and its app-server. The contract says what every Driver does; these specifications say how this one does it, and carry the requirements only this Driver has.

Conventions (shape of a specification, requirement identifiers, origin, checks, status, decisions) are defined once in the [contract's README](../../arbol/driver-contract/README.md#conventions). Identifiers here start with `CDX`; the specification number matches the contract's.

Source Refs name enabled repositories only. Evidence from the frozen version 1 repository or corpus uses ordinary Markdown links or `arbol_deprecated_v1:path#symbol` locators, never machine-readable source declarations or provenance edges. Active references to the Driver Contract remain Source Refs.

| Spec | Title | Refines | Status |
|---|---|---|---|
| [CDX-0](00-overview-and-legacy-map.md) | Overview and legacy map | DRV-0 | accepted |
| [CDX-1](01-subscriptions.md) | Subscriptions | DRV-1 | accepted |
| [CDX-2](02-inference.md) | Inference | DRV-2 | accepted |
| [CDX-3](03-tools-and-permissions.md) | Tools and permissions | DRV-3 | accepted |
| [CDX-4](04-errors-and-limits.md) | Errors and limits | DRV-4 | accepted |

Current numbered Build verification: `research/first-working-build-2026-10-07/verification.json` (SYL-94, working Build `1`, package `1.0.0`, all 128 units and 38 shared scenarios, one test-account message, and failed Build `2` preserving the default). Earlier complete-suite and candidate verification remains in `research/conformance-2026-10-07/verification.json` (SYL-92).

Evidence the specifications rest on is in `research/`: the [inventory of the version 1 Driver](../research/v1-driver-inventory.md) and the [record of probes against the installed tool](../research/tool-probes-2026-10-05.md).

## Browser producer amendment · 14 November 2026

[CDX-1.17](01-subscriptions.md#browser-lifetime-proof-refinement--14-november-2026) and shared DRV-0.17/DRV-1.28–1.30/DRV-6.17–6.20 add the unimplemented revision-1 Subscription lifetime producer. Earlier package/Build evidence remains valid only for its recorded scope and supplies no identity-format-2 pass. Producer implementation and qualification are ABR-34/ABR-38 of the Arbol Browser Saga; no installed migration occurs in the specification amendment.
