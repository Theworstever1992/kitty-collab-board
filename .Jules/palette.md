## 2025-05-14 - Semantic Navigation in Icon-Heavy Dashboards
**Learning:** Using clickable list items (`<li>`) for navigation in a sidebar is a common anti-pattern that breaks keyboard accessibility and screen reader semantics. Replacing them with semantic `<button>` or `<a>` elements ensures they are naturally focusable and have the correct role.
**Action:** Always prefer semantic interactive elements (`<button>`, `<a>`) over generic tags with click listeners. Use `aria-current` to indicate the active link/page in navigation structures.

## 2025-05-14 - Context for Icon-Only Badges
**Learning:** Visual-only indicators like unread count badges (`1`, `5`, etc.) are ambiguous to screen readers if they lack context.
**Action:** Use a `.sr-only` class to append hidden text (e.g., `<span class="sr-only">unread messages</span>`) to badges to make them meaningful for all users.
