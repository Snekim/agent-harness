---
name: task-decomposition
description: Turn a settled implementation approach into ordered work packets with clear file ownership and verification. Use before delegating work or coordinating changes across layers.
---

# Task decomposition

Write each packet so it can be executed independently once its dependencies are met:

- User-visible result, role, and acceptance check.
- Owned paths and shared files that only the parent may edit.
- Interface assumptions, upstream dependencies, and tests the worker should run.
- Return: changed paths, test results, and decisions or blockers for the parent.

Settle interfaces before splitting work by layer. Run packets together only when their writes are disjoint and neither needs the other's unfinished changes. Keep integration tests and resolution of conflicting edits with the parent. Use one packet for a task that does not benefit from a split.
