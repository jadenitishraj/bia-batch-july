#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# This removes this demo's trips, instance, volumes, site buckets and CDN.
# The bootstrap state bucket and CI identity are removed separately at the end.
mkdir -p build
python3 scripts/package_backend.py build/backend.tar.gz
export TF_VAR_backend_archive="$PWD/build/backend.tar.gz"
terraform -chdir=terraform init -input=false \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=travel-demo/terraform.tfstate" \
  -backend-config="region=us-east-1" -backend-config="use_lockfile=true"
terraform -chdir=terraform destroy -input=false -auto-approve
