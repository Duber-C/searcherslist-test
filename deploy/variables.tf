variable "aws_region" {
  description = "AWS region for the stack."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as prefix for resources."
  type        = string
  default     = "searchers-backend"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.50.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs for EC2."
  type        = list(string)
  default     = ["10.50.1.0/24", "10.50.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs for RDS."
  type        = list(string)
  default     = ["10.50.101.0/24", "10.50.102.0/24"]
}

variable "instance_type" {
  description = "EC2 instance type for Django."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 30
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to reach SSH."
  type        = list(string)
  default     = []
}

variable "ssh_public_key" {
  description = "Optional public SSH key for the EC2 instance."
  type        = string
  default     = ""
  sensitive   = true
}

variable "repository_full_name" {
  description = "Repository in owner/name format for CodePipeline."
  type        = string
}

variable "repository_branch" {
  description = "Branch deployed by the pipeline."
  type        = string
  default     = "main"
}

variable "codestar_connection_arn" {
  description = "ARN of an existing CodeStar connection to GitHub."
  type        = string
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "app"
}

variable "db_username" {
  description = "PostgreSQL admin username."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL admin password."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB for PostgreSQL."
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "18"
}

variable "db_backup_retention_period" {
  description = "Days to retain RDS automated backups."
  type        = number
  default     = 7
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for the RDS instance."
  type        = bool
  default     = false
}

variable "db_deletion_protection" {
  description = "Enable deletion protection on the RDS instance."
  type        = bool
  default     = true
}

variable "app_port" {
  description = "Gunicorn port inside the container."
  type        = number
  default     = 8000
}

variable "django_env" {
  description = "Key/value pairs written to the Django production env file."
  type        = map(string)
  default     = {}
  sensitive   = true
}
