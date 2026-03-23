data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

locals {
  name = "${var.project_name}-${var.environment}"

  azs = slice(
    data.aws_availability_zones.available.names,
    0,
    min(length(data.aws_availability_zones.available.names), 2)
  )

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  default_django_env = {
    DEBUG                          = "False"
    DJANGO_SETTINGS_MODULE         = "searcher_api.settings"
    APP_PORT                       = tostring(var.app_port)
    POSTGRES_PORT                  = "5432"
    AWS_STORAGE_BUCKET_NAME_STATIC = aws_s3_bucket.static.bucket
    AWS_STORAGE_BUCKET_NAME_MEDIA  = aws_s3_bucket.media.bucket
    AWS_S3_REGION_NAME             = var.aws_region
  }

  merged_django_env = merge(local.default_django_env, var.django_env)

  django_env_file = join(
    "\n",
    [for key in sort(keys(local.merged_django_env)) : "${key}=${local.merged_django_env[key]}"]
  )

  db_env_file = join(
    "\n",
    [
      "POSTGRES_DB=${var.db_name}",
      "POSTGRES_USER=${var.db_username}",
      "POSTGRES_PASSWORD=${var.db_password}",
      "POSTGRES_HOST=${aws_db_instance.postgres.address}",
      "POSTGRES_PORT=${aws_db_instance.postgres.port}",
    ]
  )
}

