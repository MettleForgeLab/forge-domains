# Bundle Format

A bundle is a versioned directory containing:

- bundle.yaml manifest
- roles/
- domains/
- rituals/
- atlases/
- tests/test_scrolls/

Bundles must validate deterministically.
No bundle may redefine governance invariants or mechanism contracts.
