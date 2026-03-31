variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
}

variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "searcherlist"
}

variable "environment" {
  description = "Deployment environment (dev or prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Must be 'dev' or 'prod'."
  }
}

# --- Networking ---

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ, used by RDS)"
  type        = list(string)
}

variable "availability_zones" {
  description = "Availability zones to use (must match subnet count)"
  type        = list(string)
}

# --- EC2 ---

variable "ec2_instance_type" {
  description = "EC2 instance type for the Django app server"
  type        = string
}

variable "ec2_key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "ec2_ami_id" {
  description = "AMI ID for the EC2 instance (Amazon Linux 2023 recommended)"
  type        = string
  default     = "ami-0cb5cf49019e79c51" # Amazon Linux 2023, us-east-1
}

# --- Security ---

variable "allowed_ssh_cidrs" {
  description = "CIDRs allowed to SSH into the EC2 instance. Empty list disables SSH access."
  type        = list(string)
  default     = []
}

variable "allowed_db_cidrs" {
  description = "CIDRs allowed to connect to RDS directly (e.g. 0.0.0.0/0 for dev). Empty disables public DB access."
  type        = list(string)
  default     = []
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
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
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

variable "rds_publicly_accessible" {
  description = "Make RDS publicly accessible. Enable in dev to allow connections from local."
  type        = bool
  default     = false
}

# --- Django App ---

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "django_debug" {
  description = "Enable Django DEBUG mode. Should be false in prod."
  type        = bool
  default     = false
}

variable "django_allowed_hosts" {
  description = "Space-separated list of ALLOWED_HOSTS"
  type        = string
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS_ALLOWED_ORIGINS"
  type        = string
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
}

# --- S3 ---

variable "media_bucket_name" {
  description = "S3 bucket name for Django media files (must be globally unique)"
  type        = string
}

variable "static_bucket_name" {
  description = "S3 bucket name for Django static files (must be globally unique)"
  type        = string
}
