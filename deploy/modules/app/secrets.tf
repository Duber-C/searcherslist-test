##############################################################################
# Secrets Manager — app secrets
##############################################################################

resource "aws_secretsmanager_secret" "app" {
  name                    = "${var.project_name}-${var.environment}-app-secrets"
  recovery_window_in_days = 0

  tags = { Name = "${var.project_name}-${var.environment}-app-secrets" }
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    SECRET_KEY             = var.django_secret_key
    DEBUG                  = var.django_debug ? "True" : "False"
    ALLOWED_HOSTS          = var.django_allowed_hosts
    CORS_ALLOWED_ORIGINS   = var.cors_allowed_origins
    CSRF_TRUSTED_ORIGINS   = "https://${var.django_allowed_hosts}"
    DJANGO_SETTINGS_MODULE = "config.settings.${var.environment}"

    POSTGRES_DB       = var.db_name
    POSTGRES_USER     = var.db_username
    POSTGRES_PASSWORD = var.db_password
    POSTGRES_HOST     = aws_db_instance.postgres.address
    POSTGRES_PORT     = tostring(aws_db_instance.postgres.port)

    AWS_STORAGE_BUCKET_NAME = var.media_bucket_name
    AWS_S3_CUSTOM_DOMAIN    = ""
    AWS_S3_REGION_NAME      = var.aws_region
    STATICFILES_BUCKET      = var.static_bucket_name

    OPENAI_API_KEY = var.openai_api_key
  })
}
