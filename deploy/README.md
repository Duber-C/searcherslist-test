# Searcherlist — AWS Infrastructure (Terraform)

Deploys the Django backend to AWS using EC2, RDS, S3, ECR, and CodePipeline.

---

## Architecture

```
GitHub
  │
  └── CodePipeline
        ├── CodeBuild  →  builds Docker image, pushes to ECR
        └── CodeDeploy →  pulls image from ECR, runs migrations + collectstatic, starts containers

EC2 (Docker Compose — Django + Gunicorn + Nginx)
  ├── reads/writes  →  S3 media bucket      (private)
  ├── collectstatic →  S3 static bucket     (public-read, via django-storages)
  └── connects to   →  RDS PostgreSQL       (private subnet)
```

| Resource | Purpose |
|---|---|
| **EC2** (`t3.small`) | Runs Docker Compose: Django/Gunicorn + Nginx containers |
| **ECR** | Stores built Docker images |
| **RDS** PostgreSQL 16 | Application database (private subnet, encrypted) |
| **S3** `searcherlist-media-prod` | User-uploaded media files (private) |
| **S3** `searcherlist-static-prod` | Collected static files (public-read, via django-storages) |
| **CodePipeline** | CI/CD — triggered on push to `main` |
| **CodeBuild** | Builds Docker image, pushes to ECR |
| **CodeDeploy** | Deploys to EC2 — pulls image, runs collectstatic + migrate, starts containers |
| **VPC** | Isolated network with public + private subnets across 2 AZs |

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with sufficient permissions
- An existing **EC2 Key Pair** in your target region (`us-east-1`)
- A **GitHub personal access token** with `repo` and `admin:repo_hook` scopes

---

## Deployment Steps

### 1. Create an ECR repository

```bash
aws ecr create-repository --repository-name searchers-backend --region us-east-1
```

Note the repository URI from the output — you'll need it in step 3.

---

### 2. Configure Terraform variables

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

### 3. Set ECR repo name in buildspec

In `buildspec.yml`, update the `ECR_REPO_NAME` variable to match the repository name you created in step 1:

```yaml
env:
  variables:
    ECR_REPO_NAME: searchers-backend  # update this if you used a different name
```

---

### 4. Grant CodeBuild permissions to push to ECR

The CodeBuild IAM role needs the following ECR permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:BatchCheckLayerAvailability",
    "ecr:InitiateLayerUpload",
    "ecr:UploadLayerPart",
    "ecr:CompleteLayerUpload",
    "ecr:PutImage"
  ],
  "Resource": "*"
}
```

Add this to the CodeBuild IAM role in `iam.tf` or via the AWS Console.

---

### 5. Create `.env.production` on the EC2 instance

SSH into the instance and create `/app/.env.production` with all required environment variables:

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@<ec2_public_ip>
sudo nano /app/.env.production
```

Required variables:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=your-django-secret-key
POSTGRES_HOST=<rds-endpoint>
POSTGRES_DB=searcherlist
POSTGRES_USER=searcherlist
POSTGRES_PASSWORD=strong-password-here
POSTGRES_PORT=5432
OPENAI_API_KEY=sk-...
AWS_STORAGE_BUCKET_NAME=searcherlist-static-prod
AWS_S3_REGION_NAME=us-east-1
```

> For a more secure approach, pull secrets from AWS Secrets Manager or Parameter Store in `deploy/scripts/after_install.sh` instead of maintaining a file on disk.

---

### 6. Initialize and apply Terraform

```bash
terraform init
terraform plan   # review before applying
terraform apply
```

Type `yes` when prompted. This will take ~5–10 minutes (RDS takes the longest).

---

### 7. Point your DNS

After apply completes, grab the Elastic IP:

```bash
terraform output ec2_public_ip
```

Create an **A record** in your DNS provider:

| Name | Type | Value |
|---|---|---|
| `api.searcherlist.com` | A | `<ec2_public_ip>` |

---

### 8. Trigger the first deployment

Push to the `main` branch (or re-run the pipeline manually in the AWS Console under **CodePipeline**). The pipeline will:

1. Pull source from GitHub
2. Build the Docker image via CodeBuild
3. Push the image to ECR
4. Deploy to EC2 via CodeDeploy:
   - Pull the new image from ECR
   - Run `collectstatic` (uploads to S3)
   - Run `migrate`
   - Start Django + Nginx containers via Docker Compose

---

## Deploy flow per commit

```
git push origin main
  │
  ├── CodeBuild
  │     ├── docker build -f compose/Dockerfile
  │     ├── docker push → ECR
  │     └── writes image URI to deploy/.image
  │
  └── CodeDeploy (on EC2)
        ├── AfterInstall:
        │     ├── docker pull <image>
        │     ├── docker run → collectstatic
        │     └── docker run → migrate
        └── ApplicationStart:
              └── docker compose up -d  (Django + Nginx)
```

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
├── user_data.sh              # EC2 bootstrap: installs Docker, Docker Compose, CodeDeploy agent
├── scripts/
│   ├── after_install.sh      # pulls image, runs collectstatic + migrate
│   └── start_app.sh          # docker compose up
└── terraform.tfvars.example  # Template for your tfvars

# Repo root (used by CodePipeline):
buildspec.yml                 # CodeBuild: builds and pushes Docker image to ECR
appspec.yml                   # CodeDeploy: lifecycle hooks
prod.yml                      # Docker Compose config for production
compose/
├── Dockerfile                # Django app image
├── start-django              # Container entrypoint: starts Gunicorn
├── start-celery              # Container entrypoint: starts Celery
└── nginx.conf                # Nginx config
```

---

## Useful Commands

```bash
# SSH into the EC2 instance
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw ec2_public_ip)

# View Django container logs
docker compose -f /app/prod.yml logs -f django

# View Nginx container logs
docker compose -f /app/prod.yml logs -f nginx

# Manually run a migration
source /app/deploy/.image
docker run --rm --env-file /app/.env.production $ECR_IMAGE python manage.py migrate

# Open a Django shell
source /app/deploy/.image
docker run --rm -it --env-file /app/.env.production $ECR_IMAGE python manage.py shell

# Restart containers
cd /app && docker compose -f prod.yml restart

# Destroy all infrastructure (irreversible — prompts for confirmation)
terraform destroy
```

---

## Notes

- **RDS deletion protection** is enabled by default. You must disable it in `rds.tf` before running `terraform destroy`.
- **Static files** are uploaded to S3 by `collectstatic` at deploy time (not served by Nginx). Configure `django-storages` with `AWS_STORAGE_BUCKET_NAME` and `STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'` in your prod settings.
- **Media files** are private. Configure `django-storages` with pre-signed URLs to serve them through Django.
- To store Terraform state remotely (recommended for teams), uncomment the `backend "s3"` block in `main.tf` and create the state bucket first.
- The `.image` file written by CodeBuild contains the exact ECR image URI used for the current deployment. It is sourced by all deploy scripts to ensure consistency.
