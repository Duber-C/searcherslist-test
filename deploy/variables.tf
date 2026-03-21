variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for AWS resource names."
  type        = string
  default     = "searchers-backend"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public EC2 subnet."
  type        = string
  default     = "10.20.1.0/24"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private RDS subnets. Must contain at least two subnets in different AZs."
  type        = list(string)
  default     = ["10.20.11.0/24", "10.20.12.0/24"]
}

variable "availability_zones" {
  description = "Availability zones used by the subnets. Must match the number of private subnets."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "instance_type" {
  description = "EC2 instance type for Django."
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Optional EC2 key pair name for SSH access."
  type        = string
  default     = null
}

variable "allowed_ssh_cidrs" {
  description = "CIDR ranges allowed to reach EC2 over SSH."
  type        = list(string)
  default     = []
}

variable "app_port" {
  description = "Internal container port exposed by gunicorn."
  type        = number
  default     = 8000
}

variable "repo_url" {
  description = "Git repository URL that EC2 should clone during bootstrap."
  type        = string
}

variable "repo_branch" {
  description = "Git branch, tag, or ref to deploy."
  type        = string
  default     = "main"
}

variable "enable_codepipeline" {
  description = "Whether to create CodePipeline and CodeBuild for automated deployments."
  type        = bool
  default     = false
}

variable "pipeline_branch" {
  description = "Repository branch watched by CodePipeline."
  type        = string
  default     = "main"
}

variable "codestar_connection_arn" {
  description = "AWS CodeStar connection ARN used by CodePipeline to read the Git repository."
  type        = string
  default     = null
}

variable "pipeline_repo_owner" {
  description = "Source repository owner or organization for CodePipeline."
  type        = string
  default     = null
}

variable "pipeline_repo_name" {
  description = "Source repository name for CodePipeline."
  type        = string
  default     = null
}

variable "codebuild_compute_type" {
  description = "CodeBuild compute size for deployments."
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
}

variable "codebuild_image" {
  description = "Managed CodeBuild image used for deployment jobs."
  type        = string
  default     = "aws/codebuild/standard:7.0"
}

variable "artifact_bucket_force_destroy" {
  description = "Whether the CodePipeline artifact bucket should be force-destroyed."
  type        = bool
  default     = false
}

variable "app_dir" {
  description = "Directory on the instance where the app will be checked out."
  type        = string
  default     = "/opt/searchers-backend"
}

variable "django_settings_module" {
  description = "Django settings module used by gunicorn."
  type        = string
  default     = "searcher_api.settings"
}

variable "django_secret_key" {
  description = "Django SECRET_KEY."
  type        = string
  sensitive   = true
}

variable "debug" {
  description = "Django DEBUG flag."
  type        = bool
  default     = false
}

variable "allowed_hosts" {
  description = "Django ALLOWED_HOSTS."
  type        = list(string)
}

variable "cors_allowed_origins" {
  description = "Django CORS_ALLOWED_ORIGINS."
  type        = list(string)
  default     = []
}

variable "csrf_trusted_origins" {
  description = "Django CSRF_TRUSTED_ORIGINS."
  type        = list(string)
  default     = []
}

variable "chat_gpt_secret_key" {
  description = "Application CHAT_GPT_SECRET_KEY env var."
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "Application OPENAI_API_KEY env var."
  type        = string
  default     = ""
  sensitive   = true
}

variable "email_backend" {
  description = "Django EMAIL_BACKEND value."
  type        = string
  default     = "django.core.mail.backends.console.EmailBackend"
}

variable "enable_django_ses" {
  description = "Configure the app to use django-ses and attach SES send permissions to the EC2 role."
  type        = bool
  default     = true
}

variable "ses_identity_arn" {
  description = "Optional SES identity ARN to scope sending permissions. Leave null to allow sending from any verified identity in the account."
  type        = string
  default     = null
}

variable "default_from_email" {
  description = "Django DEFAULT_FROM_EMAIL value."
  type        = string
  default     = "support@searcherlist.com"
}

variable "aws_access_key_id" {
  description = "Optional AWS access key exposed to the app."
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "Optional AWS secret access key exposed to the app."
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_ses_region_name" {
  description = "SES region name used by the app."
  type        = string
  default     = "us-east-1"
}

variable "aws_ses_region_endpoint" {
  description = "Optional SES endpoint override. Leave null to derive it from the SES region."
  type        = string
  default     = null
}

variable "db_name" {
  description = "RDS database name."
  type        = string
  default     = "postgres"
}

variable "db_username" {
  description = "RDS master username."
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Optional RDS master password. Leave null to generate one."
  type        = string
  default     = null
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for Postgres in GB."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum autoscaled storage for Postgres in GB."
  type        = number
  default     = 100
}

variable "db_engine_version" {
  description = "Postgres engine version."
  type        = string
  default     = "18"
}

variable "db_multi_az" {
  description = "Whether to deploy the RDS instance in Multi-AZ mode."
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "RDS automated backup retention in days."
  type        = number
  default     = 7
}

variable "db_skip_final_snapshot" {
  description = "Skip final snapshot when destroying RDS."
  type        = bool
  default     = false
}

variable "db_final_snapshot_identifier" {
  description = "Optional final snapshot identifier to use when destroying RDS with snapshots enabled."
  type        = string
  default     = null
}

variable "db_deletion_protection" {
  description = "Enable deletion protection on the RDS instance."
  type        = bool
  default     = true
}

variable "create_elastic_ip" {
  description = "Whether to allocate and associate an Elastic IP with the EC2 instance."
  type        = bool
  default     = true
}
