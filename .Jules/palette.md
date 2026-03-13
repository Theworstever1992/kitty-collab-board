## 2025-03-13 - [Fix UI Unresponsiveness]
**Learning:** Using `time.sleep()` for a delayed polling loop in a `curses` interface using `stdscr.nodelay(True)` fundamentally breaks input responsiveness. It causes keystrokes to be ignored or heavily delayed by the sleep block.
**Action:** Always replace `stdscr.nodelay(True)` with `stdscr.timeout(milliseconds)` when a fixed refresh rate is needed alongside immediate input responses.
