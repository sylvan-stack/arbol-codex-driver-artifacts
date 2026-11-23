---
role: authored
---
# Justifications

## <before state_format>

Removed: Capture and compare local Subscription lifetime proof under the canonical short lock without authentication or vendor work

Removed by Intention i-ae52ca5d · 2026-11-15

## IdentityState

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## IdentityState.check

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## IdentityState.check_guard

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## IdentityState.close

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityState.lock

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## IdentityState.open

Reason: Require format 2 in normal Codex Driver state admission while preserving exclusive conversion.

Origins: DRV-6.17, DRV-6.18 · Intention i-1118c20b · 2026-11-23

## _prepare_directory

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## _qualified

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## _sync

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## root_generation

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## state_format

Reason: Hold stable local format-2 admission and initialize durable root identity before ordinary state access

Origins: DRV-6.17, DRV-6.18, DRV-6.19, DRV-6.21 · Intention i-c58ed4c9 · 2026-11-15

## <before canonical_id>

Reason: Bind private account progress and reaping to the captured Subscription lifetime as well as its original owner and attempt

Origins: DRV-6.17, DRV-6.20, DRV-1.29, CDX-1.17 · Intention i-128ca76c · 2026-11-15

## IdentityState.capture_proof

Reason: Capture and compare local Subscription lifetime proof under the canonical short lock without authentication or vendor work

Origins: DRV-1.28, DRV-1.29, DRV-1.30, DRV-6.17, CDX-1.17 · Intention i-ae52ca5d · 2026-11-15

## IdentityState.require_proof

Reason: Capture and compare local Subscription lifetime proof under the canonical short lock without authentication or vendor work

Origins: DRV-1.28, DRV-1.29, DRV-1.30, DRV-6.17, CDX-1.17 · Intention i-ae52ca5d · 2026-11-15

## canonical_id

Reason: Capture and compare local Subscription lifetime proof under the canonical short lock without authentication or vendor work

Origins: DRV-1.28, DRV-1.29, DRV-1.30, DRV-6.17, CDX-1.17 · Intention i-ae52ca5d · 2026-11-15

## expected_proof

Reason: Capture and compare local Subscription lifetime proof under the canonical short lock without authentication or vendor work

Origins: DRV-1.28, DRV-1.29, DRV-1.30, DRV-6.17, CDX-1.17 · Intention i-ae52ca5d · 2026-11-15

## IdentityJournal

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal._directory

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal._matching_sidecar

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal._pending

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal._record_present

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal._same

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal.begin_remove

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal.cancel_remove

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal.complete_remove

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal.pending

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## IdentityJournal.settle

Reason: Conservatively retire only the archived target journal witness under its canonical lock without changing account records or credentials

Origins: DRV-6.17, DRV-6.18, DRV-6.20, DRV-1.29, DRV-1.30 · Intention i-cdfcc1e8 · 2026-11-15

## PendingIdentity

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## PendingIdentity.document

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## PendingIdentity.parse

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## subscription_sidecar

Reason: Implement exact create/remove identity journal validation and conservative durable settlement under the caller short lock

Origins: DRV-1.29, DRV-1.30, DRV-6.17, DRV-6.20, CDX-1.17 · Intention i-1ab80fe7 · 2026-11-15

## LifetimeSnapshot

Reason: Carry an explicit internal lifetime snapshot through delayed record and usage updates while preserving public records

Origins: DRV-1.29, DRV-1.30, DRV-6.20, CDX-1.17 · Intention i-37786378 · 2026-11-15

## LifetimeSnapshot.capture

Reason: Carry an explicit internal lifetime snapshot through delayed record and usage updates while preserving public records

Origins: DRV-1.29, DRV-1.30, DRV-6.20, CDX-1.17 · Intention i-37786378 · 2026-11-15

## lifetime_matches

Reason: Bind private account progress and reaping to the captured Subscription lifetime as well as its original owner and attempt

Origins: DRV-6.17, DRV-6.20, DRV-1.29, CDX-1.17 · Intention i-128ca76c · 2026-11-15

## LifetimeSnapshot.document

Reason: Bind private account progress and reaping to the captured Subscription lifetime as well as its original owner and attempt

Origins: DRV-6.17, DRV-6.20, DRV-1.29, CDX-1.17 · Intention i-128ca76c · 2026-11-15

## LifetimeSnapshot.parse

Reason: Bind private account progress and reaping to the captured Subscription lifetime as well as its original owner and attempt

Origins: DRV-6.17, DRV-6.20, DRV-1.29, CDX-1.17 · Intention i-128ca76c · 2026-11-15

## RecoveryObservation

Reason: Recover only unchanged dead progress under fresh admission and keep stale delayed results out of ordinary reaping

Origins: DRV-6.2, DRV-6.4, DRV-6.6, DRV-6.10, DRV-6.17, DRV-6.19, DRV-6.20, DRV-1.29, CDX-1.8, CDX-1.17 · Intention i-b5245024 · 2026-11-15

## RecoveryObservation.capture

Reason: Recover only unchanged dead progress under fresh admission and keep stale delayed results out of ordinary reaping

Origins: DRV-6.2, DRV-6.4, DRV-6.6, DRV-6.10, DRV-6.17, DRV-6.19, DRV-6.20, DRV-1.29, CDX-1.8, CDX-1.17 · Intention i-b5245024 · 2026-11-15

## retire_pending

Reason: Conservatively retire only the archived target journal witness under its canonical lock without changing account records or credentials

Origins: DRV-6.17, DRV-6.18, DRV-6.20, DRV-1.29, DRV-1.30 · Intention i-cdfcc1e8 · 2026-11-15

