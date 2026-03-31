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

  user_data_base64 = base64encode(templatefile("${path.module}/user_data.sh", {
    secret_name = aws_secretsmanager_secret.app.name
    aws_region  = var.aws_region
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
