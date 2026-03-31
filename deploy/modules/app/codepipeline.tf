##############################################################################
# CodeDeploy — Application + Deployment Group
##############################################################################

resource "aws_codedeploy_app" "django" {
  name             = "${var.project_name}-${var.environment}"
  compute_platform = "Server"
}

resource "aws_codedeploy_deployment_group" "django" {
  app_name              = aws_codedeploy_app.django.name
  deployment_group_name = "${var.project_name}-${var.environment}-group"
  service_role_arn      = aws_iam_role.codedeploy.arn

  deployment_config_name = "CodeDeployDefault.AllAtOnce"

  ec2_tag_set {
    ec2_tag_filter {
      key   = "Name"
      type  = "KEY_AND_VALUE"
      value = "${var.project_name}-${var.environment}-django"
    }
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }

  deployment_style {
    deployment_option = "WITHOUT_TRAFFIC_CONTROL"
    deployment_type   = "IN_PLACE"
  }
}

##############################################################################
# CodeBuild
##############################################################################

resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/aws/codebuild/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

resource "aws_codebuild_project" "django" {
  name          = "${var.project_name}-${var.environment}-build"
  description   = "Build, test, and package the Django application"
  build_timeout = 20
  service_role  = aws_iam_role.codebuild.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:8.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true

    environment_variable {
      name  = "STATIC_BUCKET"
      value = var.static_bucket_name
    }

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.codebuild.name
      status     = "ENABLED"
    }
  }

  tags = { Name = "${var.project_name}-${var.environment}-build" }
}

##############################################################################
# CodeStar Connection — GitHub v2
##############################################################################

resource "aws_codestarconnections_connection" "github" {
  name          = "${var.project_name}-${var.environment}-github"
  provider_type = "GitHub"

  tags = { Name = "${var.project_name}-${var.environment}-github-connection" }
}

##############################################################################
# CodePipeline
##############################################################################

resource "aws_codepipeline" "django" {
  name     = "${var.project_name}-${var.environment}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.artifacts.bucket
    type     = "S3"
  }

  # ── Stage 1: Source ──────────────────────────────────────────────────────
  stage {
    name = "Source"

    action {
      name             = "GitHub_Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn        = aws_codestarconnections_connection.github.arn
        FullRepositoryId     = "${var.github_owner}/${var.github_repo}"
        BranchName           = var.github_branch
        OutputArtifactFormat = "CODE_ZIP"
      }
    }
  }

  # ── Stage 2: Build ───────────────────────────────────────────────────────
  stage {
    name = "Build"

    action {
      name             = "CodeBuild"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.django.name
      }
    }
  }

  # ── Stage 3: Deploy ──────────────────────────────────────────────────────
  stage {
    name = "Deploy"

    action {
      name            = "CodeDeploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CodeDeploy"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ApplicationName     = aws_codedeploy_app.django.name
        DeploymentGroupName = aws_codedeploy_deployment_group.django.deployment_group_name
      }
    }
  }
}
