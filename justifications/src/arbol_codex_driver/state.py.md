---
role: authored
---
# Justifications

## <before Owner>

Reason: Validate legacy record file descriptors before reading without blocking on special files or changing JSON semantics

Origins: DRV-6.17, DRV-6.18 · Intention i-951fe407 · 2026-11-15

## Owner

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## State.__init__

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## State.clear_unfinished_writes

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## State.initialize

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## State.subscription

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## <before default_state_directory>

Removed: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Removed by Intention i-c58ed4c9 · 2026-11-15

## State.assert_admitted

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## State.close

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## read_json

Reason: Validate legacy record file descriptors before reading without blocking on special files or changing JSON semantics

Origins: DRV-6.17, DRV-6.18 · Intention i-951fe407 · 2026-11-15

