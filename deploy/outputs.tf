output "ec2_public_ip" {
  value = aws_eip.app.public_ip
}

output "ec2_public_dns" {
  value = aws_instance.app.public_dns
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "static_bucket_name" {
  value = aws_s3_bucket.static.bucket
}

output "media_bucket_name" {
  value = aws_s3_bucket.media.bucket
}

output "artifacts_bucket_name" {
  value = aws_s3_bucket.artifacts.bucket
}

output "codepipeline_name" {
  value = aws_codepipeline.app.name
}

output "codedeploy_app_name" {
  value = aws_codedeploy_app.app.name
}

