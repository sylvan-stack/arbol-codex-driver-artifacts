---
role: authored
---
# Justifications

## AppServer.start

Reason: Launch Codex through its own installed package while preserving its existing local account and state identity

Origins: CDX-0.3, DRV-0.8, DRV-0.15 · Intention i-4cb0c94a · 2026-11-27

## validate_driver_config

Removed: Use the native Codex app-server defaults and owner approval boundary for Arbol runs.

Removed by Intention i-30e1d5ae · 2026-11-25

## <before write_driver_config>

Removed: Apply only the four accepted per-process Codex options, without writing configuration or forcing credential storage.

Removed by Intention i-92a77207 · 2026-11-14

## write_driver_config

Removed: Apply only the four accepted per-process Codex options, without writing configuration or forcing credential storage.

Removed by Intention i-92a77207 · 2026-11-14

## <before validate_driver_config>

Removed: Move startup identity ledger into admitted parent and gate unchanged vendor exec on durable orphan evidence

Removed by Intention i-96473a98 · 2026-11-15

## <before startup_ledger>

Reason: Launch Codex through its own installed package while preserving its existing local account and state identity

Origins: CDX-0.3, DRV-0.8, DRV-0.15 · Intention i-4cb0c94a · 2026-11-27

## startup_ledger

Reason: Move startup identity ledger into admitted parent and gate unchanged vendor exec on durable orphan evidence

Origins: DRV-6.20, DRV-6.21, DRV-6.18, CDX-1.17 · Intention i-96473a98 · 2026-11-15

## rpc_failure

Reason: Use the real default Codex account and preserve typed refusal before any alternate native route starts.

Origins: CDX-1.2, CDX-1.10, DRV-1.11, OG-5 · Intention i-0a5490e3 · 2026-11-21

## AppServer.__init__

Reason: Use the native Codex app-server defaults and owner approval boundary for Arbol runs.

Origins: OG-8 · Intention i-30e1d5ae · 2026-11-25

