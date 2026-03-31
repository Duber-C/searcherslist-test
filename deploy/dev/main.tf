provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "searcherlist"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "app" {
  source = "../modules/app"

  # --- General ---
  aws_region   = var.aws_region
  project_name = "searcherlist"
  environment  = "dev"

  # --- Networking ---
  # Use a different CIDR than prod to avoid conflicts
  vpc_cidr             = "10.1.0.0/16"
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b"]

  # --- EC2 ---
  ec2_instance_type = "t3.micro"
  ec2_key_pair_name = var.ec2_key_pair_name

  # --- Security: open access for local testing ---
  allowed_ssh_cidrs       = ["0.0.0.0/0"]
  allowed_db_cidrs        = ["0.0.0.0/0"]
  rds_publicly_accessible = true

  # --- RDS ---
  db_instance_class = "db.t3.micro"
  db_password       = var.db_password

  # --- Django ---
  django_secret_key    = var.django_secret_key
  django_debug         = true
  django_allowed_hosts = var.django_allowed_hosts
  cors_allowed_origins = var.cors_allowed_origins
  openai_api_key       = var.openai_api_key

  # --- S3 ---
  media_bucket_name  = "searcherlist-media-dev"
  static_bucket_name = "searcherlist-static-dev"

  # --- CI/CD: triggers on the dev branch ---
  github_owner  = var.github_owner
  github_repo   = var.github_repo
  github_branch = var.github_branch
}
