#!/usr/bin/env python3
import os, sys, json, yaml
from pathlib import Path
from jsonschema import Draft202012Validator

REQ_DIRS = ["roles", "domains", "rituals", "atlases", "tests/test_scrolls"]

def fail(msg):
    print(msg)
    sys.exit(1)

def load_yaml(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def validate_schema(obj: dict, schema_path: Path, label: str):
    schema = load_json(schema_path)
    v = Draft202012Validator(schema)
    errs = sorted(v.iter_errors(obj), key=lambda e: e.path)
    if errs:
        msgs=[]
        for e in errs[:10]:
            path=".".join([str(x) for x in e.path]) or "(root)"
            msgs.append(f"{label} {path}: {e.message}")
        fail("schema validation failed:\n" + "\n".join(msgs))

def main():
    bundle = Path(sys.argv[1] if len(sys.argv) > 1 else "bundles/home")
    manifest_path = bundle / "bundle.yaml"
    if not manifest_path.exists():
        fail(f"Missing {manifest_path}")

    for d in REQ_DIRS:
        p = bundle / d
        if not p.exists():
            fail(f"Missing required dir: {p}")

    manifest = load_yaml(manifest_path)

    # schema validate bundle.yaml
    schema_bundle = Path("schemas/bundle_manifest.schema.json")
    if not schema_bundle.exists():
        fail(f"Missing {schema_bundle}")
    validate_schema(manifest, schema_bundle, "bundle.yaml")

    contents = (manifest.get("contents") or {})

    # ensure referenced files exist
    for section in ["roles", "domains", "rituals", "atlases", "tests"]:
        for rel in contents.get(section, []) or []:
            p = bundle / rel
            if not p.exists():
                fail(f"Manifest entry missing: {p}")

    # schema validate all content files
    schema_role = Path("schemas/role_scroll.schema.json")
    schema_domain = Path("schemas/domain_scroll.schema.json")
    schema_ritual = Path("schemas/ritual_scroll.schema.json")
    schema_atlas = Path("schemas/atlas.schema.json")

    role_ids=set()
    for rel in contents.get("roles", []) or []:
        p=bundle/rel
        d=load_yaml(p)
        validate_schema(d, schema_role, str(p))
        rid=d.get("role_id")
        if not rid: fail(f"{p} missing role_id")
        if rid in role_ids: fail(f"Duplicate role_id: {rid}")
        role_ids.add(rid)

    domain_files = contents.get("domains", []) or []
    domain_ids=set()
    priorities=[]
    by_id={}
    for rel in domain_files:
        p=bundle/rel
        d=load_yaml(p)
        validate_schema(d, schema_domain, str(p))
        did=d.get("domain_id")
        if not did: fail(f"{p} missing domain_id")
        lo=(d.get("load_order") or {})
        pr=lo.get("priority")
        if pr is None or not isinstance(pr,int):
            fail(f"{p} missing load_order.priority (int)")
        if did in domain_ids: fail(f"Duplicate domain_id: {did}")
        domain_ids.add(did)
        priorities.append((pr,did,rel))
        by_id[did]=pr

    if priorities and "DOMAIN:HOME" in by_id:
        min_pr = sorted(priorities, key=lambda x: x[0])[0][0]
        if by_id["DOMAIN:HOME"] != min_pr:
            fail(f"DOMAIN:HOME must have minimum priority (found {by_id['DOMAIN:HOME']}, min {min_pr})")

    # enforce HOME < KINFORM < GUARDIAN < HOUSEHOLD < GRID if present
    order = ["DOMAIN:HOME","DOMAIN:KINFORM","DOMAIN:GUARDIAN","DOMAIN:HOUSEHOLD","DOMAIN:GRID"]
    for a,b in zip(order, order[1:]):
        if a in by_id and b in by_id and not (by_id[a] < by_id[b]):
            fail(f"Expected {a} priority < {b} priority")

    ritual_ids=set()
    for rel in contents.get("rituals", []) or []:
        p=bundle/rel
        d=load_yaml(p)
        validate_schema(d, schema_ritual, str(p))
        rid=d.get("ritual_id")
        if not rid: fail(f"{p} missing ritual_id")
        if rid in ritual_ids: fail(f"Duplicate ritual_id: {rid}")
        ritual_ids.add(rid)

    atlas_ids=set()
    for rel in contents.get("atlases", []) or []:
        p=bundle/rel
        d=load_yaml(p)
        validate_schema(d, schema_atlas, str(p))
        aid=d.get("atlas_id")
        if not aid: fail(f"{p} missing atlas_id")
        if aid in atlas_ids: fail(f"Duplicate atlas_id: {aid}")
        atlas_ids.add(aid)

    # reference integrity: domains binding roles and inherits_from
    for rel in domain_files:
        p=bundle/rel
        d=load_yaml(p)
        bindings=(d.get("bindings") or {})
        roles=(bindings.get("roles") or {})
        referenced=set()
        if isinstance(roles, list):
            referenced.update(roles)
        elif isinstance(roles, dict):
            for _,v in roles.items():
                if isinstance(v, list):
                    referenced.update(v)
        missing_roles=[r for r in referenced if r and r not in role_ids]
        if missing_roles:
            fail(f"{p} references roles not in bundle: {missing_roles}")

        inh=(bindings.get("inherits_from") or {})
        inh_dom=inh.get("domain")
        if inh_dom and inh_dom not in domain_ids:
            fail(f"{p} inherits_from domain {inh_dom} not present")

        atl=(bindings.get("atlases") or {})
        if isinstance(atl, dict):
            for _,v in atl.items():
                if isinstance(v,str) and v.startswith("ATLAS:") and v not in atlas_ids:
                    fail(f"{p} references atlas_id not in bundle: {v}")

    print("OK")

if __name__ == "__main__":
    main()