provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "searcherlist"
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

module "app" {
  source = "../modules/app"

  # --- General ---
  aws_region   = var.aws_region
  project_name = "searcherlist"
  environment  = "prod"

  # --- Networking ---
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b"]

  # --- EC2 ---
  ec2_instance_type = "t3.small"
  ec2_key_pair_name = var.ec2_key_pair_name

  # --- Security: no SSH, no public DB access ---
  allowed_ssh_cidrs       = []
  allowed_db_cidrs        = []
  rds_publicly_accessible = false

  # --- RDS ---
  db_instance_class = "db.t3.micro"
  db_password       = var.db_password

  # --- Django ---
  django_secret_key    = var.django_secret_key
  django_debug         = false
  django_allowed_hosts = var.django_allowed_hosts
  cors_allowed_origins = var.cors_allowed_origins
  openai_api_key       = var.openai_api_key

  # --- S3 ---
  media_bucket_name  = "searcherlist-media-prod"
  static_bucket_name = "searcherlist-static-prod"

  # --- CI/CD: triggers on the main branch ---
  github_owner  = var.github_owner
  github_repo   = var.github_repo
  github_branch = var.github_branch
}
