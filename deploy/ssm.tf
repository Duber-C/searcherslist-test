resource "aws_ssm_parameter" "django_env" {
  name      = "/${local.name}/django/env"
  type      = "SecureString"
  value     = local.django_env_file
  overwrite = true
}

resource "aws_ssm_parameter" "db_env" {
  name      = "/${local.name}/django/db"
  type      = "SecureString"
  value     = local.db_env_file
  overwrite = true
}

