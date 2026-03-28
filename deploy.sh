#!/usr/bin/env bash
# Deploy the birthday SMS Lambda using AWS SAM
# Prerequisites: aws cli, sam cli, pip
# Usage: ./deploy.sh

set -euo pipefail

STACK_NAME="birthday-sms"
REGION="${AWS_REGION:-us-west-2}"
S3_DEPLOY_BUCKET="${S3_DEPLOY_BUCKET:-}"  # SAM needs a bucket to upload the package

echo "==> Installing dependencies into package/"
rm -rf package
pip install -r requirements.txt -t package/ --quiet
cp lambda_function.py package/
cp contacts.json package/

echo "==> Building SAM package"
sam build --use-container 2>/dev/null || sam build

echo "==> Prompting for TextBelt API key"
read -rsp "TextBelt API key: " TEXTBELT_KEY
echo

echo "==> Deploying stack: $STACK_NAME to $REGION"
sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --parameter-overrides \
    "TextBeltApiKey=$TEXTBELT_KEY" \
  --no-confirm-changeset

echo ""
echo "Deployment complete!"
echo "The Lambda will fire every day at 08:00 UTC (midnight PST / 1 AM PDT)."
echo ""
echo "To test immediately:"
echo "  aws lambda invoke --function-name birthday-sms-sender --region $REGION out.json && cat out.json"
