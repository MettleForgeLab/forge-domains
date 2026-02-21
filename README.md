# forge-domains

**Layer:** content  
**Scope:** Declarative domain/role/ritual/atlas bundles for ForgeOS.  
**Non-scope:** No control math, no routing, no runtime orchestration, no enforcement logic.

This repo defines _what exists_ in a LaForge node.
It does not define _how behavior is computed_ or _how invariants are enforced_.

## Hard boundaries

forge-domains MUST NOT:

- implement routing logic
- compute gain/readiness
- enforce event membrane
- mutate runtime state
- read runtime logs/model outputs/UI state

forge-domains MUST:

- declare unique IDs (role_id, domain_id, ritual_id, atlas_id)
- encode deterministic load order (domains)
- validate bundle structure deterministically
- avoid dangling references

Upstream: forgeos-mechanisms (schemas/contracts), governance stack  
Downstream: chest-engine, weave-observer-ui, ops-verification
