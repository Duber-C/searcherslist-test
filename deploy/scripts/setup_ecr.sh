#!/bin/bash
set -e

# -----------------------------------------------
# ECR Setup Script
# Usage: ./deploy/scripts/setup_ecr.sh
#
# Requires: AWS CLI configured with sufficient permissions
# -----------------------------------------------

REPO_NAME="searchers-backend"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
KEEP_IMAGES=5

echo "==> Fetching AWS account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME"

# 1. Create ECR repository (skip if already exists)
echo "==> Creating ECR repository '$REPO_NAME'..."
if aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" > /dev/null 2>&1; then
  echo "    Repository already exists, skipping."
else
  aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION" > /dev/null
  echo "    Created: $ECR_URI"
fi

# 2. Apply lifecycle policy
echo "==> Applying lifecycle policy (keep last $KEEP_IMAGES images)..."
aws ecr put-lifecycle-policy \
  --repository-name "$REPO_NAME" \
  --region "$REGION" \
  --lifecycle-policy-text "{
    \"rules\": [{
      \"rulePriority\": 1,
      \"selection\": {
        \"tagStatus\": \"any\",
        \"countType\": \"imageCountMoreThan\",
        \"countNumber\": $KEEP_IMAGES
      },
      \"action\": { \"type\": \"expire\" }
    }]
  }" > /dev/null
echo "    Done."

# 3. Authenticate Docker with ECR
echo "==> Logging Docker into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# 4. Update buildspec.yml with ECR_REPO_NAME
BUILDSPEC="$(git rev-parse --show-toplevel)/buildspec.yml"
if grep -q "ECR_REPO_NAME:" "$BUILDSPEC"; then
  sed -i "s|ECR_REPO_NAME:.*|ECR_REPO_NAME: $REPO_NAME|" "$BUILDSPEC"
  echo "==> Updated ECR_REPO_NAME in buildspec.yml."
fi

# 5. Print summary
echo ""
echo "✔  ECR setup complete."
echo ""
echo "   Repository URI : $ECR_URI"
echo "   Region         : $REGION"
echo "   Lifecycle      : keep last $KEEP_IMAGES images"
echo ""
echo "Next steps:"
echo "  1. Ensure your CodeBuild IAM role has ECR push permissions"
echo "  2. Ensure your EC2 IAM instance profile has ECR pull permissions"
echo "  3. See deploy/README.md for the full IAM policy snippets"
