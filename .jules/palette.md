## 2025-04-04 - ARIA labels added

**Learning:** When making code edits that only involve UI components and no other logic, such as adding `aria-label`, make sure not to inadvertently commit generated build artifacts like `frontend/dist/` or `frontend/node_modules/.vite/deps/` alongside source code changes. Doing so creates unnecessary bloat and conflicts.

**Action:** Before requesting a code review or submitting the final patch, always double-check `git status` or `git diff --cached` to verify that only the intended source code files are included in the staging area and build files are correctly excluded or not staged.