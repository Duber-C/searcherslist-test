# Non-secret variables with sensible prod defaults

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "ec2_key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
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

# --- Secrets (set in terraform.tfvars, never commit) ---

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}
