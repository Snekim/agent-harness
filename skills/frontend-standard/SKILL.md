---
name: frontend-standard
description: Apply frontend coding standards when implementing or reviewing web UI, forms, client state, or API integration. Use the existing framework, design system, and architecture.
---

# Frontend standard

- Read nearby screens and project rules first. Reuse existing UI primitives, styles, data clients, and state ownership. Preserve public slice imports if the project uses Feature-Sliced Design; do not add layers for a small feature.
- Give each state one owner. Use local state for transient UI, URL state for shareable navigation, and the existing query cache for remote data. Derive values from their source instead of keeping a second copy in sync.
- Render the states the flow can actually reach: loading, empty, failure, and submitting. Preserve input on recoverable errors and prevent duplicate submissions when a write is pending.
- Use native controls with accessible names and labels. Keep keyboard focus visible; if a dialog changes focus, check where it returns on close. Communicate errors and state through text as well as color.
- Keep types at the boundary accurate. Use the agreed API contract and handle network or parsing failures explicitly. Avoid casts or lint suppression that conceal a mismatch.
- Run the relevant lint, type, and behavior checks. For visible or interactive changes, exercise the affected flow with keyboard input and a narrow viewport when browser tools are available. Report any unverified states.
