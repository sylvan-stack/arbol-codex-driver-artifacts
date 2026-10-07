---
role: authored
---
# Codex Driver specifications

How `arbol-codex-driver` meets the [Driver Contract](../../arbol/driver-contract/README.md) with the `codex` command-line tool and its app-server. The contract says what every Driver does; these specifications say how this one does it, and carry the requirements only this Driver has.

Conventions (shape of a specification, requirement identifiers, origin, checks, status, decisions) are defined once in the [contract's README](../../arbol/driver-contract/README.md#conventions). Identifiers here start with `CDX`; the specification number matches the contract's.

| Spec | Title | Refines | Status |
|---|---|---|---|
| [CDX-0](00-overview-and-legacy-map.md) | Overview and legacy map | DRV-0 | implemented |
| [CDX-1](01-subscriptions.md) | Subscriptions | DRV-1 | implemented |
| [CDX-2](02-inference.md) | Inference | DRV-2 | implemented |
| [CDX-3](03-tools-and-permissions.md) | Tools and permissions | DRV-3 | implemented |
| [CDX-4](04-errors-and-limits.md) | Errors and limits | DRV-4 | implemented |

Current numbered Build verification: `research/first-working-build-2026-10-07/verification.json` (SYL-94, working Build `1`, package `1.0.0`, all 128 units and 38 shared scenarios, one test-account message, and failed Build `2` preserving the default). Earlier complete-suite and candidate verification remains in `research/conformance-2026-10-07/verification.json` (SYL-92).

Evidence the specifications rest on is in `research/`: the [inventory of the version 1 Driver](../research/v1-driver-inventory.md) and the [record of probes against the installed tool](../research/tool-probes-2026-10-05.md).
