# Kitty Collab Board — Native App (Tauri)

Native desktop application using Tauri.

## Setup

```bash
cd native-app
npm install
cargo build --release
```

## Features

- System tray integration
- Native notifications
- Offline-first sync with backend
- Real-time task updates
- Agent health monitoring
- Dark mode support

## Development

```bash
# Watch mode
npm run tauri dev

# Build
npm run tauri build

# Test on specific platform
cargo test --all
```

## Architecture

- **Frontend:** React 18 + TypeScript (shared with web)
- **Backend:** Tauri (Rust) with system tray + notifications
- **Data:** SQLite local cache with async sync to backend
- **IPC:** Tauri commands for board operations

## Status

✅ Scaffold created
⬜ System tray integration
⬜ Native notifications
⬜ Offline sync
⬜ Cross-platform testing
