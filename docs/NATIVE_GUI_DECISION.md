# TASK 6051 — Native GUI: Tauri vs Electron Decision

**Date:** 2026-03-07
**Author:** Claude
**Status:** Decision made — Tauri recommended

---

## Context

The web frontend (`web/frontend/`) is a Vite+React+TypeScript app that runs in a browser tab. A native desktop app would enable:

- System tray icon with real-time task badge
- Desktop notifications when tasks complete or agents go offline
- Offline-first operation (no browser needed)
- OS-level integration (keyboard shortcuts, dock badges)

Two viable frameworks: **Tauri** (Rust + WebView) and **Electron** (Node.js + Chromium).

---

## Evaluation

### Bundle Size

| Framework | Typical binary size |
|-----------|-------------------|
| Tauri | 3–10 MB |
| Electron | 80–200 MB |

Tauri wins significantly. Clowder is a background utility — a 150MB download is a poor first impression.

### Memory Usage

| Framework | Idle RAM |
|-----------|---------|
| Tauri | ~30–50 MB |
| Electron | ~150–250 MB |

Tauri uses the OS's native WebView (WebKit on macOS/Linux, Edge WebView2 on Windows) instead of shipping Chromium. This matters for a tool that runs continuously in the tray.

### Performance

Both frameworks render the same React UI, so UI performance is identical. Tauri's native backend (Rust) is faster for file system operations, though the bottleneck in Clowder is always the board JSON file access.

### Development Experience

- **Tauri**: `cargo` + `npm`. Requires Rust toolchain. `tauri dev` hot-reloads the frontend. Rust backend gives type-safe native APIs.
- **Electron**: Pure Node.js — if the team knows JS, zero learning curve. Larger community, more plugins.

For Clowder, the native backend is minimal: watch `board.json` for changes, send desktop notifications, manage tray. Neither framework has a learning-curve advantage here — the FS watching can use Tauri's built-in `tauri-plugin-fs` or Electron's Node.js `fs.watch`.

### Security

Tauri has a strict CSP and a smaller attack surface (no Node.js in renderer). Electron exposes a full Node.js runtime to the renderer process, which is a real attack vector (relevant for apps loading remote content). Clowder loads no remote content, but Tauri's model is cleaner regardless.

### Cross-Platform Support

| Framework | macOS | Linux | Windows |
|-----------|-------|-------|---------|
| Tauri | ✅ | ✅ | ✅ (WebView2 required) |
| Electron | ✅ | ✅ | ✅ |

Tauri requires WebView2 on Windows, which is bundled with Windows 11 and auto-installed on Windows 10 via the runtime installer. This is a minor friction point for Windows users.

### System Tray

Both frameworks support system tray natively. Tauri's `tauri-plugin-shell` and tray APIs are well-documented. Electron's `Tray` class is battle-tested.

### Desktop Notifications

Both support OS notifications. Tauri uses `tauri-plugin-notification`. Electron uses the web Notifications API or `node-notifier`. Equivalent.

---

## Decision: Tauri

**Recommendation: Build with Tauri.**

Rationale:
1. **Bundle size** is the deciding factor. Clowder is a utility app. Shipping 150MB for a task-board TUI is unjustifiable.
2. **Memory footprint** matters for a permanently-running tray app.
3. **Security model** is better by default.
4. **Rust dependency** is a one-time setup cost, not an ongoing burden — the Rust backend will be < 200 lines.
5. The existing React frontend (`web/frontend/`) is reused directly as the Tauri frontend — no migration needed.

The only real Tauri downside (WebView2 on Windows) is minor — it's pre-installed on most Windows 10+ machines.

---

## Proposed Architecture

```
clowder-desktop/            # Tauri app (new directory)
├── src-tauri/
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs         # Tauri entry point, tray setup
│       ├── board_watcher.rs  # FS watch board.json → emit events
│       └── notifications.rs  # Desktop notification dispatch
├── src/                    # Symlink or copy of web/frontend/src
├── index.html
├── package.json
└── tauri.conf.json
```

### Native Backend Responsibilities (Rust)

- Watch `board.json` for changes (notify crate)
- Emit `board_update` Tauri events to frontend
- Send OS desktop notifications on task completion or agent offline
- Manage system tray icon + badge count (pending tasks)
- Read `CLOWDER_BOARD_DIR` env var on startup

### Frontend

The existing React frontend is reused. When running in Tauri:
- WebSocket calls to `ws://localhost:8000` are replaced by Tauri event listeners
- The API server becomes optional — Tauri can read board.json directly

---

## Task Breakdown (next steps for 6052–6055)

| Task | Description |
|------|-------------|
| 6052 | Scaffold Tauri app, wire up existing React frontend |
| 6053 | System tray: icon, badge count (pending tasks), right-click menu |
| 6054 | Desktop notifications: task done, agent offline, handoff request |
| 6055 | Offline-first: Tauri reads board.json directly, no API dependency |

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Rust toolchain setup friction | Document in DEPLOYMENT.md; one-time cost |
| WebView2 not present on Windows | Ship runtime installer link; Tauri auto-prompts |
| Board file path differs per install | Read `CLOWDER_BOARD_DIR` env var, fallback to `~/clowder/board` |
| WebView rendering differences across OS | Test on all three platforms in CI |
