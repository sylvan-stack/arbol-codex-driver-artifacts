# Probe scripts of 6 October 2026

The scripts behind the addenda of 6 October 2026 in `../tool-probes-2026-10-05.md`, kept as records of what was run against the installed `codex`. They are not maintained tools.

- `probe/common.py`: the clean environment and the helper that reads a child's JSON lines.
- `probe/`: checks without a login or with the owner's own setup.
- `live/`: checks on the signed-in test account; each run starts in an empty folder under `live/work-*`. Run from inside `live/`. They spend a little quota.
- `signin/`: the sign-in as a Driver will do it. The paths written `<this folder>` were absolute paths of a temporary folder.
- `live/codex-all.json`: every notification of the real runs of `live/t_codex.py`, with the account's address, identifiers and home folder replaced.
