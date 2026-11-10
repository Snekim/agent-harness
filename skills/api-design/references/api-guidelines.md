# API guidelines

- Write one success and one failure example with exact HTTP status and body shape. State whether null, omission, and empty values differ.
- Adding a required request field, removing a response field, tightening validation, and changing status or error shape can break callers. Trace consumers before making the change; use a compatible rollout or versioning when needed.
- If a request can repeat after a timeout, say whether it is safe to retry and what identifies a duplicate operation. For lists, preserve stable ordering across page boundaries when adding pagination.
- Agree which failure modes are public. Keep authentication, authorization, missing resources, and validation consistent with nearby endpoints and the project's disclosure rules.
