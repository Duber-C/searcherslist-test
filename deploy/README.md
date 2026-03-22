# AWS Terraform Deployment

This Terraform template deploys:

- One EC2 instance for the Django app
- One PostgreSQL RDS instance
- Optional django-ses email through Amazon SES
- Optional CodePipeline + CodeBuild for continuous deployment
- A dedicated VPC with one public subnet for EC2 and two private subnets for RDS
- Security groups that only allow PostgreSQL access from the EC2 instance

## What it does

The EC2 bootstrap script:

- installs Docker and Git
- clones this repository
- writes `.env.production`, `.env.db`, and `.env.compose`
- deploys the repo's `prod.yml`
- runs Django with migrations and `collectstatic`

When `enable_django_ses = true`, the template also:

- sets the app email backend to `django_ses.SESBackend`
- passes SES region config into Django
- grants the EC2 role permission to send mail via SES

When `enable_codepipeline = true`, the template also creates:

- a versioned S3 artifact bucket
- a CodePipeline source stage using CodeStar Connections
- a CodeBuild deploy stage

The deploy stage uses AWS Systems Manager to run commands on the EC2 instance so the server checks out the new commit and runs `docker compose up -d --build`.
The deploy stage uses `prod.yml` and starts only the `django` service so production keeps using RDS instead of a local Postgres container.

The application is exposed on port `80` directly from the container. If you want TLS, place CloudFront, an ALB, or nginx in front of the instance.

## Files

- `versions.tf`: Terraform and provider versions
- `main.tf`: AWS infrastructure
- `variables.tf`: Inputs
- `outputs.tf`: Useful outputs after apply
- `user_data.sh.tftpl`: EC2 bootstrap script
- `buildspec-deploy.yml`: CodeBuild deployment steps
- `terraform.tfvars.example`: Example variable values

## Usage

1. Copy the example vars file.

```bash
cd deploy
cp terraform.tfvars.example terraform.tfvars
```

2. Update at minimum:

- `repo_url`
- `django_secret_key`
- `allowed_hosts`
- `allowed_ssh_cidrs`

If you want CI/CD too, also set:

- `enable_codepipeline = true`
- `codestar_connection_arn`
- `pipeline_repo_owner`
- `pipeline_repo_name`

If you want SES email too, also confirm:

- `enable_django_ses = true`
- `default_from_email` is a verified SES sender
- `ses_identity_arn` matches your SES identity if you want least-privilege IAM

3. Initialize and apply.

```bash
terraform init
terraform plan
terraform apply
```

## Important assumptions

- `repo_url` must be reachable from the EC2 instance. The included bootstrap uses `git clone`.
- If CodePipeline is enabled, you must create and authorize the AWS CodeConnections connection first. Older CodeStar connection ARNs also work.
- If SES is enabled, the sender identity must already be verified in Amazon SES.
- The current production deployment uses `prod.yml`, which builds from `compose/Dockerfile`.
- The template expects Django to keep using:
  - `POSTGRES_DB`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`

## Operational notes

- If `db_password` is omitted, Terraform generates one. You can retrieve it with:

```bash
terraform output -raw generated_db_password
```

- RDS deletion protection is enabled by default.
- Destroy will require `db_deletion_protection = false`.
- If you want SSH access, create an AWS key pair first and set `key_name`.
- The pipeline deploys by asking SSM to update the checked-out repository on the EC2 instance and run `docker compose --env-file .env.compose -f prod.yml up -d --build --no-deps django`.
- The SSM deploy step assumes the EC2 host is already bootstrapped with `git`, Docker, and Docker Compose; if those prerequisites are missing, the deploy fails fast instead of trying to provision the server during deployment.
- The EC2 bootstrap installs Docker Compose with the Linux CLI plugin layout under `/usr/local/lib/docker/cli-plugins/docker-compose` instead of relying on the Amazon Linux package repository.
- `user_data_replace_on_change = true` is enabled so Terraform replaces the EC2 instance when bootstrap logic changes.
- Static AWS app credentials are not required for SES if you use the EC2 instance role created by this template.

## Recommended follow-up

- Attach a domain to the EC2 public IP or Elastic IP.
- Add TLS termination with an ALB or nginx plus ACM/certbot.
- Move app secrets from plain Terraform variables into SSM Parameter Store or Secrets Manager.
