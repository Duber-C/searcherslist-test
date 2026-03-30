# Searcherlist — AWS Infrastructure (Terraform)

Deploys the Django backend to AWS using EC2, RDS, S3, and CodePipeline.

---

## Architecture

```
GitHub
  │
  └── CodePipeline
        ├── CodeBuild  →  runs tests, syncs staticfiles/ to S3
        └── CodeDeploy →  deploys code to EC2, runs migrations, restarts gunicorn

EC2 (Django + Gunicorn + Nginx)
  ├── reads/writes  →  S3 media bucket      (private)
  ├── serves from   →  S3 static bucket     (public-read)
  └── connects to   →  RDS PostgreSQL       (private subnet)
```

| Resource | Purpose |
|---|---|
| **EC2** (`t3.small`) | Django app server — Gunicorn + Nginx |
| **RDS** PostgreSQL 16 | Application database (private subnet, encrypted) |
| **S3** `searcherlist-media-prod` | User-uploaded media files (private) |
| **S3** `searcherlist-static-prod` | Collected static files (public-read) |
| **CodePipeline** | CI/CD — triggered on push to `main` |
| **CodeBuild** | Runs tests, collectstatic, syncs to S3 |
| **CodeDeploy** | Deploys artifact to EC2, runs migrations |
| **VPC** | Isolated network with public + private subnets across 2 AZs |

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with sufficient permissions
- An existing **EC2 Key Pair** in your target region (`us-east-1`)
- A **GitHub personal access token** with `repo` and `admin:repo_hook` scopes

---

## Deployment Steps

### 1. Configure variables

```bash
cd deploy/
cp terraform.tfvars.example terraform.tfvars
```

Open `terraform.tfvars` and fill in all required values:

```hcl
# AWS
aws_region   = "us-east-1"
project_name = "searcherlist"
environment  = "prod"

# EC2
ec2_key_pair_name = "your-key-pair-name"

# RDS
db_password = "strong-password-here"

# Django
django_secret_key    = "your-django-secret-key"
django_allowed_hosts = "api.searcherlist.com"
cors_allowed_origins = "https://www.searcherlist.com"
openai_api_key       = "sk-..."

# S3 — names must be globally unique
media_bucket_name  = "searcherlist-media-prod"
static_bucket_name = "searcherlist-static-prod"

# GitHub
github_owner       = "your-github-username-or-org"
github_repo        = "searchers-backend"
github_branch      = "main"
github_oauth_token = "ghp_..."
```

> **Never commit `terraform.tfvars`** — it contains secrets. It is already listed in `.gitignore`.

---

### 2. Initialize Terraform

```bash
terraform init
```

---

### 3. Review the plan

```bash
terraform plan
```

Review the output to confirm resources before creating anything.

---

### 4. Apply

```bash
terraform apply
```

Type `yes` when prompted. This will take ~5–10 minutes (RDS takes the longest).

---

### 5. Point your DNS

After apply completes, grab the Elastic IP from the output:

```bash
terraform output ec2_public_ip
```

Create an **A record** in your DNS provider:

| Name | Type | Value |
|---|---|---|
| `api.searcherlist.com` | A | `<ec2_public_ip>` |

---

### 6. Trigger the first deployment

Push to the `main` branch (or re-run the pipeline manually in the AWS Console under **CodePipeline**). The pipeline will:

1. Pull source from GitHub
2. Run tests via CodeBuild
3. Sync `staticfiles/` to S3
4. Deploy code to EC2 via CodeDeploy
5. Run `python manage.py migrate`
6. Restart Gunicorn

---

## File Structure

```
deploy/
├── main.tf                   # Terraform provider and backend config
├── variables.tf              # All input variables
├── outputs.tf                # Useful values after apply (IP, endpoints, etc.)
├── vpc.tf                    # VPC, subnets, internet gateway, route tables
├── security_groups.tf        # EC2 (80/443/22) and RDS (5432 from EC2 only)
├── iam.tf                    # IAM roles for EC2, CodeBuild, CodeDeploy, CodePipeline
├── s3.tf                     # media, static, and pipeline artifact buckets
├── rds.tf                    # RDS PostgreSQL instance and subnet group
├── ec2.tf                    # EC2 instance and Elastic IP
├── codepipeline.tf           # CodeDeploy, CodeBuild, CodePipeline, GitHub webhook
├── user_data.sh              # EC2 bootstrap: installs nginx, gunicorn, CodeDeploy agent
├── scripts/
│   ├── after_install.sh      # pip install, migrate, collectstatic (runs on EC2 via CodeDeploy)
│   ├── start_app.sh          # restart gunicorn, reload nginx
│   └── validate.sh           # health check after deploy
└── terraform.tfvars.example  # Template for your tfvars

# Repo root (used by CodePipeline):
buildspec.yml                 # CodeBuild instructions
appspec.yml                   # CodeDeploy instructions
```

---

## Useful Commands

```bash
# SSH into the EC2 instance
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw ec2_public_ip)

# View Gunicorn logs on the server
sudo journalctl -u gunicorn -f

# View Nginx logs on the server
sudo tail -f /var/log/nginx/error.log

# Manually run a migration on the server
sudo -u django bash -c "source /app/venv/bin/activate && cd /app/src && python manage.py migrate"

# Destroy all infrastructure (irreversible — prompts for confirmation)
terraform destroy
```

---

## Notes

- **RDS deletion protection** is enabled by default. You must disable it in `rds.tf` before running `terraform destroy`.
- The **media bucket** is private. To serve media files directly from S3 (instead of through Django), configure `django-storages` with pre-signed URLs.
- The **static bucket** is public-read. Update `STATIC_URL` in your Django settings to point to the bucket URL shown in `terraform output static_bucket_url`.
- To store Terraform state remotely (recommended for teams), uncomment the `backend "s3"` block in `main.tf` and create the state bucket first.
