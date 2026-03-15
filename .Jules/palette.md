## 2026-03-14 - [UX TUI Update]
**Learning:** The TUI in `mission_control.py` uses `time.sleep(3)` in `curses_loop`,
which makes the UI unresponsive to user input (like 'q' or 'a') for up to 3 seconds.
To fix this, using `stdscr.timeout()` instead of `time.sleep(3)` improves responsiveness
by waiting for input without entirely blocking the event loop.
**Action:** Replaced `time.sleep(3)` with `stdscr.timeout(3000)`.
