# Terraform template for Django DRF on AWS

This folder provisions a base AWS stack for this API with:

- `EC2` for the application server
- `RDS PostgreSQL`
- `S3` bucket for `static`
- `S3` bucket for `media`
- `CodePipeline + CodeBuild + CodeDeploy` for CI/CD

The application is deployed on the EC2 instance with Docker Compose, and the container keeps the code under `/app`, matching the current `compose/Dockerfile`.

## Files

- `*.tf`: infrastructure definition
- `buildspec.yml`: artifact packaging for `CodeBuild`
- `docker-compose.aws.yml`: runtime compose file for EC2
- `codedeploy/`: deployment hooks and `appspec.yml`

## Required variables

Copy `terraform.tfvars.example` to `terraform.tfvars` and fill at least:

- `repository_full_name`
- `codestar_connection_arn`
- `db_password`
- `django_env.SECRET_KEY`
- `django_env.ALLOWED_HOSTS`

## Usage

```bash
cd deploy
terraform init
terraform plan
terraform apply
```

## Important note about S3

This template creates the S3 buckets and injects their names in the Django environment, but the current Django settings still store `static` and `media` on local disk. To actually serve them from S3 you still need to wire Django storage backends, usually with `django-storages` and bucket-based `STATICFILES_STORAGE` / `DEFAULT_FILE_STORAGE` (or the Django 5 `STORAGES` setting).
