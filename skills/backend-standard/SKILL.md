---
name: backend-standard
description: Apply backend coding standards when implementing or reviewing server-side logic, HTTP handlers, persistence, jobs, or migrations. Use the project's existing stack and boundaries.
---

# Backend standard

- Find the project instructions, nearest comparable feature, and its tests. Identify the request or event contract and the owner of each persistence operation before editing.
- Validate and authorize at the entry boundary. Put business decisions in the existing service or domain layer. Keep storage and transport details behind the project's existing interfaces; avoid introducing a new layer for one call.
- Preserve status codes, error shape, and default behavior for existing callers. Use `$api-design` if the public HTTP contract changes. Do not turn an internal exception into a client-facing stack trace or log sensitive payloads.
- Keep related writes in one transaction when they must succeed together. For retryable requests and jobs that can repeat side effects, define how duplicates are prevented; test the repeat path when it matters.
- For schema changes, consider running old and new code against the same database during rollout. Verify the migration in a disposable database using the project's migration tool.
- Test observable behavior at the narrowest real boundary: cover the normal path and the specific rejection, conflict, or retry behavior changed. Report commands and any untested behavior.
