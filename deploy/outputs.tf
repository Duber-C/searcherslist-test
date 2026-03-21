output "ec2_instance_id" {
  description = "EC2 instance ID running Django."
  value       = aws_instance.django.id
}

output "ec2_public_ip" {
  description = "Public IP for the Django EC2 instance."
  value       = var.create_elastic_ip ? aws_eip.django[0].public_ip : aws_instance.django.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS for the Django EC2 instance."
  value       = aws_instance.django.public_dns
}

output "rds_endpoint" {
  description = "RDS Postgres endpoint."
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS Postgres port."
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name."
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Database username."
  value       = aws_db_instance.postgres.username
}

output "generated_db_password" {
  description = "Generated DB password when var.db_password is null."
  value       = var.db_password == null ? random_password.db_password.result : null
  sensitive   = true
}

output "codepipeline_name" {
  description = "CodePipeline name when enabled."
  value       = var.enable_codepipeline ? aws_codepipeline.deploy[0].name : null
}

output "codebuild_project_name" {
  description = "CodeBuild project name when enabled."
  value       = var.enable_codepipeline ? aws_codebuild_project.deploy[0].name : null
}
