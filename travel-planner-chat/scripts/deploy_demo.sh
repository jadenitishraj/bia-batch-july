#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
python3 scripts/package_backend.py build/backend.tar.gz
npm --prefix frontend ci
npm --prefix frontend run build
export TF_VAR_backend_archive="$PWD/build/backend.tar.gz"
terraform -chdir=terraform init -input=false \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=travel-demo/terraform.tfstate" \
  -backend-config="region=us-east-1" -backend-config="use_lockfile=true"
terraform -chdir=terraform plan -input=false -out=demo.tfplan
terraform -chdir=terraform apply -input=false demo.tfplan
terraform -chdir=terraform output -json > build/deployment.json
python3 scripts/update_backend.py build/deployment.json
web_bucket=$(terraform -chdir=terraform output -raw frontend_bucket)
distribution=$(terraform -chdir=terraform output -raw distribution_id)
aws s3 sync frontend/dist/ "s3://$web_bucket/" --delete \
  --cache-control "public,max-age=31536000,immutable" --exclude index.html
aws s3 cp frontend/dist/index.html "s3://$web_bucket/index.html" \
  --cache-control "no-cache" --content-type text/html
aws cloudfront create-invalidation --distribution-id "$distribution" --paths '/*' > /dev/null
terraform -chdir=terraform output -raw website_url
