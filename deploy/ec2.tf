##############################################################################
# EC2 — Django App Server
##############################################################################

resource "aws_instance" "django" {
  ami                    = var.ec2_ami_id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_pair_name
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    project_name    = var.project_name
    environment     = var.environment
    db_host         = aws_db_instance.postgres.address
    db_port         = aws_db_instance.postgres.port
    db_name         = var.db_name
    db_user         = var.db_username
    db_password     = var.db_password
    django_secret   = var.django_secret_key
    allowed_hosts   = var.django_allowed_hosts
    cors_origins    = var.cors_allowed_origins
    media_bucket    = var.media_bucket_name
    static_bucket   = var.static_bucket_name
    aws_region      = var.aws_region
    openai_api_key  = var.openai_api_key
  }))

  tags = { Name = "${var.project_name}-${var.environment}-django" }
}

##############################################################################
# Elastic IP
##############################################################################

resource "aws_eip" "django" {
  instance = aws_instance.django.id
  domain   = "vpc"

  tags = { Name = "${var.project_name}-${var.environment}-eip" }
}
