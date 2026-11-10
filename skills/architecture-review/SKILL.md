---
name: architecture-review
description: Assess a proposed engineering change that crosses module, storage, or service boundaries. Use before implementing a structural change or settling a consequential design decision.
---

# Architecture review

1. Trace the current path from entry point to state changes and callers. Cite the existing code or contracts that constrain the change.
2. State the behavior that must change, the invariants that must hold, and which component should own the change. Identify affected public contracts and any rollout constraints.
3. Recommend the smallest approach that preserves those boundaries. Compare another approach only when the tradeoff could change the decision.
4. For each material risk, give the concrete failure and an acceptance check that would expose it. Flag missing decisions separately from details implementers can choose.
