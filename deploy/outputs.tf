output "ec2_public_ip" {
  description = "Elastic IP of the Django EC2 instance"
  value       = aws_eip.django.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.django.id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = "${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}"
}

output "media_bucket_name" {
  description = "S3 bucket for Django media files"
  value       = aws_s3_bucket.media.bucket
}

output "static_bucket_name" {
  description = "S3 bucket for Django static files"
  value       = aws_s3_bucket.static.bucket
}

output "static_bucket_url" {
  description = "Public URL for Django static files"
  value       = "https://${aws_s3_bucket.static.bucket_domain_name}"
}

output "pipeline_name" {
  description = "CodePipeline name"
  value       = aws_codepipeline.django.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
