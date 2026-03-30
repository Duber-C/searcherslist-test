variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "searcherlist"
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string
  default     = "prod"
}

# --- Networking ---

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ, used by RDS)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "Availability zones to use (must match subnet count)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# --- EC2 ---

variable "ec2_instance_type" {
  description = "EC2 instance type for the Django app server"
  type        = string
  default     = "t3.small"
}

variable "ec2_key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "ec2_ami_id" {
  description = "AMI ID for the EC2 instance (Amazon Linux 2023 recommended)"
  type        = string
  default     = "ami-0c02fb55956c7d316" # Amazon Linux 2023, us-east-1
}

# --- RDS ---

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "searcherlist"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL master password — store in terraform.tfvars or AWS Secrets Manager"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB for RDS"
  type        = number
  default     = 20
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

# --- Django App ---

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "django_allowed_hosts" {
  description = "Space-separated list of ALLOWED_HOSTS"
  type        = string
  default     = "api.searcherlist.com"
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS_ALLOWED_ORIGINS"
  type        = string
  default     = "https://www.searcherlist.com"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

# --- CodePipeline / CI-CD ---

variable "github_owner" {
  description = "GitHub repository owner (user or org)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "searchers-backend"
}

variable "github_branch" {
  description = "Branch that triggers the pipeline"
  type        = string
  default     = "main"
}

variable "github_oauth_token" {
  description = "GitHub personal access token with repo + admin:repo_hook scopes"
  type        = string
  sensitive   = true
}

# --- S3 ---

variable "media_bucket_name" {
  description = "S3 bucket name for Django media files (must be globally unique)"
  type        = string
  default     = "searcherlist-media-prod"
}

variable "static_bucket_name" {
  description = "S3 bucket name for Django static files (must be globally unique)"
  type        = string
  default     = "searcherlist-static-prod"
}
