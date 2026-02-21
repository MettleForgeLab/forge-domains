#!/usr/bin/env bash
set -euo pipefail
python3 tools/validate_bundle_layout.py bundles/home
sha256sum bundles/home/bundle.yaml
sha256sum bundles/home/roles/ROLE_HOME_v0.1.yaml
sha256sum bundles/home/domains/HOME_DOMAIN_v0.1.yaml
echo "[domain] OK"