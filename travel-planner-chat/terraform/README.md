# Temporary AWS teaching demo

One public address serves both the website and API.

```text
Browser → CloudFront → S3 (page files)
                    → EC2 Spot → Python → Bedrock (API requests)
```

CloudFront sends `/api/*` to the EC2 VPC origin. Other paths go to private S3.
The browser calls relative paths, such as `/api/chat`. No separate API domain is needed.
The EC2 public address supports outbound package downloads; API access is restricted
to CloudFront/VPC traffic. Python binds to loopback behind nginx. No SSH port is open.
The API forwards Bearer authorization and JSON content type, with caching disabled.
Cookies and browser Origin are not forwarded; this app authenticates with explicit
Bearer tokens, not automatic cookies. It has no cross-origin browser API access.

## Read these files in order

| File | Lesson |
| --- | --- |
| versions.tf | Provider, variables and remote state |
| network.tf | VPC, subnet, internet route and firewall |
| storage.tf | Private S3 buckets and source artifact |
| compute.tf | One Spot instance and its Bedrock role |
| bootstrap.sh | Install and start Python and nginx |
| cdn.tf | One domain, two origins and path routing |
| outputs.tf | Values we need after deployment |
| bootstrap/ | One-time GitHub identity and state bucket |

Terraform reads all `.tf` files in a folder together. References create dependencies.
The app state is encrypted and versioned in S3; S3 lock files prevent competing applies.
Keep local Terraform state, plans and backend settings out of Git.

## First setup

Use Terraform 1.17.1 and AWS CLI v2 with a local AWS login.

```sh
cd travel-planner-chat/terraform/bootstrap
terraform init
terraform plan -out=bootstrap.tfplan
terraform apply bootstrap.tfplan
terraform output
```

The bootstrap creates GitHub OIDC trust for this repository's `main` branch only.
PR code receives no AWS deployment credentials. No browser sign-in runs in CI.
If an AWS account already has GitHub's OIDC provider, import it before applying.

Set three GitHub **repository variables** from the bootstrap outputs:

| Variable | Value |
| --- | --- |
| AWS_REGION | us-east-1 |
| AWS_DEPLOY_ROLE_ARN | github_role_arn output |
| TF_STATE_BUCKET | state_bucket output |

No GitHub Secrets are required. No AWS access keys or Bedrock API key are stored in GitHub.
EC2 uses its instance role for Bedrock. GitHub gets short-lived credentials through OIDC.
The deployment role manages the listed AWS services in this teaching account;
its IAM write/pass permissions are limited to the backend role path.

## Deploy locally

```sh
cd travel-planner-chat
export TF_STATE_BUCKET=the-state-bucket-from-bootstrap
bash scripts/deploy_demo.sh
```

This builds the frontend, packages source without local data/secrets, prints a
saved Terraform plan, applies it, updates Python through Systems Manager, uploads
frontend files, and clears the CDN cache. Terraform prints the HTTPS site address.
Subsequent backend updates preserve SQLite accounts/trips on the instance disk.
Instance replacement or full teardown removes that local data. No shared database
or automatic backups are included in this temporary classroom deployment.

## Automatic deployment

`.github/workflows/travel-demo-deploy.yml` checks code and Terraform on PRs.
Merging into `main` runs checks, then deploys using the AWS role. Direct main pushes
also deploy. Failed checks block this workflow's deployment job.
This workflow does not configure branch protection or merge a PR for you.
Manual workflow dispatch supports `deploy` and `destroy` on main.
Deployment runs are serialized so one apply cannot interrupt another.

## Pause, resume and remove

```sh
python3 scripts/control_demo.py pause
python3 scripts/control_demo.py resume
python3 scripts/control_demo.py status
bash scripts/destroy_demo.sh
```

Pause stops compute. S3, disk storage and retained state can still cost money.
Destroy removes this demo's instance, disk, website buckets, CloudFront and network.
The buckets deliberately allow deletion of their contents: this is demo data.
Destroy is irreversible for the demo's saved trips. Spot instances can be interrupted.
There is no capacity reservation, load balancer or NAT gateway.

For complete removal, first destroy the app, then run `terraform destroy` in
`terraform/bootstrap` with the original local bootstrap state. That removes the
versioned state bucket and GitHub role, preventing future automatic redeployments.
Keep the bootstrap state until full cleanup is confirmed. Removing GitHub variables
after full cleanup makes the disabled deployment state clear.

AWS-created service-linked roles may remain; IAM roles themselves have no usage charge.
Usage already incurred is still billed. No deployment can promise a zero AWS bill.

Provider docs: [EC2](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance),
[CloudFront VPC origins](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudfront_vpc_origin).
