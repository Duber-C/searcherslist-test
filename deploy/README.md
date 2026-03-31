# Searcherlist — AWS Infrastructure (Terraform)

Deploys the Django backend to AWS using EC2, RDS, S3, ECR, and CodePipeline. Supports two isolated environments: **dev** and **prod**.

---

## Architecture

```
GitHub (branch: dev / main)
  │
  └── CodePipeline
        ├── CodeBuild  →  builds Docker image, pushes to ECR
        └── CodeDeploy →  pulls image from ECR, runs migrations + collectstatic, starts containers

EC2 (Docker Compose — Django + Gunicorn + Nginx)
  ├── reads/writes  →  S3 media bucket      (private)
  ├── collectstatic →  S3 static bucket     (public-read, via django-storages)
  └── connects to   →  RDS PostgreSQL       (private subnet)
```

| Resource | dev | prod |
|---|---|---|
| **EC2** | `t3.micro` | `t3.small` |
| **RDS** | `db.t3.micro`, publicly accessible | `db.t3.micro`, private subnet only |
| **SSH** | open (`0.0.0.0/0`) | closed |
| **DB from local** | open (`0.0.0.0/0`) | closed |
| **Django DEBUG** | `True` | `False` |
| **Branch** | `dev` | `main` |
| **VPC CIDR** | `10.1.0.0/16` | `10.0.0.0/16` |
| **S3 media** | `searcherlist-media-dev` | `searcherlist-media-prod` |
| **S3 static** | `searcherlist-static-dev` | `searcherlist-static-prod` |

---

## File Structure

```
deploy/
├── modules/
│   └── app/                      # All infrastructure logic (shared between environments)
│       ├── variables.tf
│       ├── outputs.tf
│       ├── vpc.tf
│       ├── security_groups.tf
│       ├── iam.tf
│       ├── s3.tf
│       ├── rds.tf
│       ├── ec2.tf
│       ├── codepipeline.tf
│       ├── secrets.tf
│       └── user_data.sh
├── dev/
│   ├── backend.tf                # Terraform version + provider requirements
│   ├── main.tf                   # Provider + module call with dev values
│   ├── variables.tf              # Variable declarations
│   └── terraform.tfvars.example  # Template — copy to terraform.tfvars
├── prod/
│   ├── backend.tf                # Terraform version + provider requirements
│   ├── main.tf                   # Provider + module call with prod values
│   ├── variables.tf
│   └── terraform.tfvars.example
└── scripts/
    ├── after_install.sh          # CodeDeploy: pulls image, runs collectstatic + migrate
    ├── start_app.sh              # CodeDeploy: docker compose up
    └── setup_ecr.sh              # Helper: creates ECR repo if needed

# Repo root (used by CodePipeline):
buildspec.yml                     # CodeBuild: builds and pushes Docker image to ECR
appspec.yml                       # CodeDeploy: lifecycle hooks
compose/
├── prod.yml                      # Docker Compose config for AWS environments
├── local.yml                     # Docker Compose config for local development
├── Dockerfile
├── start-django
├── start-celery
└── nginx.conf
```

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.14
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with sufficient permissions
- An existing **EC2 Key Pair** in your target region

---

## First-time Setup

### 1. Create an ECR repository

```bash
aws ecr create-repository --repository-name searchers-backend --region us-east-1
```

---

## Deploying an Environment

The steps are the same for `dev` and `prod` — just change the directory.

### 1. Configure variables

```bash
cd deploy/dev        # or deploy/prod
cp terraform.tfvars.example terraform.tfvars
```

Fill in `terraform.tfvars`:

```hcl
aws_region        = "us-east-1"
ec2_key_pair_name = "your-key-pair-name"
github_owner      = "your-github-username-or-org"
github_repo       = "searchers-backend"
github_branch     = "dev"           # "main" for prod

# Secrets
db_password       = "strong-password-here"
django_secret_key = "your-django-secret-key"
openai_api_key    = "sk-..."
```

> **Never commit `terraform.tfvars`** — it contains secrets.

Generate secure keys with:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2. Initialize and apply

```bash
terraform init
terraform plan    # review before applying
terraform apply
```

### 3. Authorize the GitHub CodeStar connection

After the first `terraform apply`, the GitHub connection will be in **Pending** state. Go to:

**AWS Console → Developer Tools → Connections** → select the connection → click **Update pending connection** and authorize with GitHub.

### 4. Point your DNS

```bash
terraform output ec2_public_ip
```

Create an **A record** in your DNS provider pointing to the Elastic IP.

### 5. Trigger the first deployment

Push to the configured branch or re-run the pipeline manually in the AWS Console under **CodePipeline**.

---

## Deploy Flow

```
git push origin dev   # or main for prod
  │
  ├── CodeBuild
  │     ├── docker build -f compose/Dockerfile
  │     ├── docker push → ECR
  │     └── writes image URI to deploy/.image
  │
  └── CodeDeploy (on EC2)
        ├── AfterInstall:
        │     ├── fetch secrets from Secrets Manager → /app/.env.production
        │     ├── docker pull <image>
        │     ├── docker run → collectstatic
        │     └── docker run → migrate
        └── ApplicationStart:
              └── docker compose -f prod.yml up -d
```

---

## Useful Commands

```bash
# SSH into dev instance (port 22 is open in dev)
ssh -i ~/.ssh/your-key.pem ec2-user@<ec2_public_ip>

# Connect to prod instance via SSM (no SSH key needed, port 22 is closed)
aws ssm start-session --target $(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=searcherlist-prod-django" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text --region us-east-1) --region us-east-1

# View Django container logs
docker compose -f /app/prod.yml logs -f django

# Manually run a migration
source /app/deploy/.image
docker run --rm --env-file /app/.env.production $ECR_IMAGE python manage.py migrate

# Open a Django shell
source /app/deploy/.image
docker run --rm -it --env-file /app/.env.production $ECR_IMAGE python manage.py shell

# Restart containers
cd /app && docker compose -f prod.yml restart

# Destroy an environment (irreversible)
cd deploy/dev && terraform destroy
```

---

## Django Settings

Each environment maps directly to a Django settings file via `DJANGO_SETTINGS_MODULE`:

| Environment | Settings file |
|---|---|
| `dev` | `config/settings/dev.py` |
| `prod` | `config/settings/prod.py` |

This value is set automatically by Terraform in Secrets Manager and injected into the container at deploy time — no manual configuration needed.

Both `dev.py` and `prod.py` configure:
- **RDS**: reads `POSTGRES_*` env vars populated from the RDS instance created by Terraform
- **S3 storage**: uses `django-storages` with S3Boto3 backend
  - `AWS_STORAGE_BUCKET_NAME` → media files (private)
  - `STATICFILES_BUCKET` → static files (public-read, uploaded via `collectstatic`)

The EC2 IAM instance profile handles S3 authentication automatically — no `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` needed for storage.

---

## Notes

- Secrets are stored in **AWS Secrets Manager** (`searcherlist-{env}-app-secrets`) and fetched automatically at deploy time — no manual `.env` file management needed.
- **Static files** are uploaded to S3 by `collectstatic` at deploy time. Configure `django-storages` in your settings.
- **Media files** are private. Use pre-signed URLs via `django-storages` to serve them.
- The `.image` file written by CodeBuild contains the exact ECR image URI used for the current deployment. It is sourced by all deploy scripts to ensure consistency.
- Dev RDS is publicly accessible — connect from local with any PostgreSQL client using the `rds_endpoint` output and the credentials from `terraform.tfvars`.
