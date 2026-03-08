# TASK 6051 — Tauri vs Electron Decision

**Sprint:** 6 | **Phase:** 11 (Native GUI) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Decision

**Tauri** — recommended and documented.

## Summary

Evaluated Tauri and Electron across: bundle size, memory, security, cross-platform support, system tray, notifications, and development experience. Full analysis in `docs/NATIVE_GUI_DECISION.md`.

Key deciding factors:
- Tauri: 3–10MB bundle vs Electron: 80–200MB — decisive for a utility/tray app
- Tauri uses OS native WebView (WebKit / Edge WebView2), not Chromium — ~30–50MB idle RAM vs 150–250MB
- Existing React frontend (`web/frontend/`) reuses directly as Tauri frontend — no migration
- Rust backend for native ops (board watching, notifications, tray) will be < 200 lines

## Proposed Architecture

`clowder-desktop/` — new directory:
- `src-tauri/src/main.rs` — tray, window, event dispatch
- `src-tauri/src/board_watcher.rs` — watch board.json, emit Tauri events
- `src-tauri/src/notifications.rs` — OS desktop notifications
- `src/` — reused React frontend

## Next Steps

- 6052: Scaffold Tauri project, wire existing React frontend
- 6053: System tray (icon, badge count, right-click menu)
- 6054: Desktop notifications (task done, agent offline, handoff)
- 6055: Offline-first (read board.json directly, no API dependency) — Qwen

## Files Created

- `docs/NATIVE_GUI_DECISION.md`
