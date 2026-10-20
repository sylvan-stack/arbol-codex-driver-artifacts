# Arbol Codex Driver: Catalog

## Chapters

### `specs/`: what this Driver does

How this Driver meets the [Driver Contract](../arbol/driver-contract/README.md) with the `codex` command-line tool. Start at the chapter's [README](specs/README.md).

- [`00-overview-and-legacy-map.md`](specs/00-overview-and-legacy-map.md) (CDX-0): what the Driver is, and where each part of the version 1 code went.
- [`01-subscriptions.md`](specs/01-subscriptions.md) (CDX-1): vendor families, home and environment per Subscription, sign-in, status, usage, model catalog.
- [`02-inference.md`](specs/02-inference.md) (CDX-2): one app-server process per run, configuration of the home, handshake and checks, threads and continuity, the mapping from notifications to events, usage, ending and stopping a run.
- [`03-tools-and-permissions.md`](specs/03-tools-and-permissions.md) (CDX-3): the parts of the tool, none of them switched off; the settings that make a run unrestricted; helper agents; the run without tools.
- [`04-errors-and-limits.md`](specs/04-errors-and-limits.md) (CDX-4): the three places a failure appears, the mapping from the tool's error class to codes, the wording fallback, retries, limit information, time limits, the tool's version.

### `research/`: evidence the specifications rest on

- [`v1-driver-inventory.md`](research/v1-driver-inventory.md): what the version 1 Driver does, read from the deprecated source, with Source Refs.
- [`tool-probes-2026-10-05.md`](research/tool-probes-2026-10-05.md): what the installed tool does, observed in real runs: handshake, account requests, model list, turns, approvals, stopping, threads, errors, configuration.
- [`probe-scripts-2026-10-06/`](research/probe-scripts-2026-10-06/README.md): the scripts behind the probes of 6 October 2026 and the raw records of one real run, kept as records of what was run against the installed `codex`.

## Conventions

- Every artifact goes into a chapter folder, never directly into the corpus root. `README.md`, `INDEX.md` and a `GLOSSARY.md` are the exceptions.
- List a chapter here when it is created.
- Tasks are tracked in Linear, not in this corpus: project [Arbol Codex Driver](https://linear.app/amorphius/project/arbol-codex-driver-468a5c06c014) in the Sylvan Stack workspace. Specifications are copied there as documents; `.linear.json` maps each file to its copy. The files here are the originals. There is no `plans/` chapter.
