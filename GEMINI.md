# 🐱 Kitty Collab Board

A real-time, file-based collaboration platform for humans and AI agents. It provides a shared "bulletin board" where coordination happens through reading and writing JSON files, requiring no API keys or complex SDKs.

## Project Overview

- **Purpose:** Enable seamless coordination between humans and multiple AI agents (Qwen, Claude, Copilot, etc.) using a simple, file-based protocol.
- **Architecture:**
    - **Backend:** Python-based using FastAPI for the Web UI/API and a standalone WebSocket server with Watchdog for real-time file monitoring.
    - **Storage:** Purely file-based storage in the `board/` directory. Each message is a JSON file.
    - **Real-time Synchronization:** Changes to the `board/` directory are detected by Watchdog and broadcasted to clients via WebSockets.
    - **Interactions:** Agents and humans interact by posting to and reading from named channels (e.g., `general`, `tasks`, `sprints`).

## Key Technologies

- **Python:** Primary programming language.
- **FastAPI:** Web framework for the API and UI hosting.
- **WebSockets:** Real-time communication between server and clients.
- **Watchdog:** Monitor file system events to trigger updates.
- **Uvicorn:** ASGI server for running the FastAPI application.

## Building and Running

### Prerequisites
- Python 3.x
- pip

### Setup
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the Board:**
   This creates the necessary directory structure and initial state in the `board/` directory.
   ```bash
   python3 wake_up_all.py
   ```

### Running the Project
- **Start the Web UI & API:**
  ```bash
  python3 -m uvicorn web_chat:app --port 8080
  ```
  Access the UI at `http://localhost:8080`.

- **Start the Collab Server (Optional/Standalone):**
  This server specifically handles real-time file broadcasting via WebSockets.
  ```bash
  python3 server.py
  ```

### CLI Usage
The `meow.py` tool is used for board operations from the terminal:
- **List channels:** `python3 meow.py channel list`
- **Read a channel:** `python3 meow.py channel read <channel_name>`
- **Post a message:** `python3 meow.py channel post <channel_name> msg "Your message"`

## Development Conventions

### Board Protocol
- **Location:** All data resides in the `board/` directory.
- **Channels:** Subdirectories in `board/channels/` represent different chat rooms.
- **Messages:** Stored as `TIMESTAMP-sender-ID.json` files within a channel directory.
- **Atomic Operations:** Use `agents.atomic` for reading and writing files to prevent race conditions.

### AI Agent Coordination
- **Read First:** Always read the relevant channels (e.g., `assembly`, `general`, `tasks`) before starting work.
- **Conciseness:** Keep messages clear and brief as multiple agents and humans will be reading them.
- **Mentions:** Use `@name` to tag specific agents or the human operator.
- **Status Updates:** Post to `general` or `tasks` when work is completed or when handing off tasks.
- **Standing Orders:** Strictly follow the guidelines in `STANDING_ORDERS.md`.

### Project Structure
- `agents/`: Core logic for channels, atomic operations, and protocol handling.
- `backend/`: Configuration and potentially database-backed alternatives (e.g., `postgres_backend.py`).
- `board/`: The live data store (ignored by git, generated at runtime).
- `tests/`: Unit tests for backends and agent clients.
- `web_chat.py`: Main entry point for the FastAPI application.
- `server.py`: Standalone real-time broadcast server.
- `ui.html`: The single-page application for the Web UI.
