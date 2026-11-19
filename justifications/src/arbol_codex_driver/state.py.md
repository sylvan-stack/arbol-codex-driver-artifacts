---
role: authored
---
# Justifications

## <before Owner>

Reason: Move the Driver default under the shared private installation without changing state-relative native homes or the override.

Origins: ARC-5.5, ARC-5.9 · Intention i-389f8a9c · 2026-11-19

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

## State.with_subscription_lock

Reason: Implement quiescent same-generation format1 upgrade and reuse the canonical short lock without normal initialization

Origins: DRV-6.17, DRV-6.18, DRV-1.30, CDX-1.17 · Intention i-12630a4b · 2026-11-15

## with_subscription_directory_lock

Reason: Implement quiescent same-generation format1 upgrade and reuse the canonical short lock without normal initialization

Origins: DRV-6.17, DRV-6.18, DRV-1.30, CDX-1.17 · Intention i-12630a4b · 2026-11-15

## read_lock

Reason: Validate independent regular nonblocking no-follow descriptors before the existing lock and orphan-owner text reads without changing their grammar or owner semantics

Origins: DRV-6.1, DRV-6.5, DRV-6.6, DRV-6.10, DRV-6.17, DRV-6.18, DRV-6.20, CDX-1.17 · Intention i-d5471a0c · 2026-11-15

## default_state_directory

Reason: Move the Driver default under the shared private installation without changing state-relative native homes or the override.

Origins: ARC-5.5, ARC-5.9 · Intention i-389f8a9c · 2026-11-19

## prepare_default_state

Reason: Move the Driver default under the shared private installation without changing state-relative native homes or the override.

Origins: ARC-5.5, ARC-5.9 · Intention i-389f8a9c · 2026-11-19

