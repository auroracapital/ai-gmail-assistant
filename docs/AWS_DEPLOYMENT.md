# AWS Lambda Deployment Guide

This guide explains how to deploy the Gmail Inbox Organizer to AWS Lambda for automated daily execution.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Gmail OAuth credentials and token (from local setup)
- OpenRouter API key

## Architecture

- **AWS Lambda**: Serverless function execution
- **AWS Secrets Manager**: Secure credential storage
- **EventBridge**: Scheduled daily triggers
- **CloudWatch Logs**: Execution logs and monitoring
- **IAM**: Least-privilege access control

## Step-by-Step Deployment

### 1. Store Secrets in AWS Secrets Manager

```bash
# Set your AWS region
export AWS_REGION=eu-west-1

# Store OpenRouter API key
aws secretsmanager create-secret \
    --name "gmail-organizer/openrouter-api-key" \
    --secret-string '{"api_key":"YOUR_OPENROUTER_API_KEY"}' \
    --tags Key=Project,Value=gmail-inbox-organizer \
    --region $AWS_REGION

# Store Gmail OAuth credentials
aws secretsmanager create-secret \
    --name "gmail-organizer/gmail-oauth-credentials" \
    --secret-string file://credentials/client_secret.json \
    --tags Key=Project,Value=gmail-inbox-organizer \
    --region $AWS_REGION

# Convert Gmail token pickle to JSON
python3 -c "
import pickle, json
with open('credentials/gmail_token.pickle', 'rb') as f:
    token = pickle.load(f)
token_dict = {
    'token': token.token,
    'refresh_token': token.refresh_token,
    'token_uri': token.token_uri,
    'client_id': token.client_id,
    'client_secret': token.client_secret,
    'scopes': token.scopes
}
with open('/tmp/gmail_token.json', 'w') as f:
    json.dump(token_dict, f)
"

# Store Gmail API token
aws secretsmanager create-secret \
    --name "gmail-organizer/gmail-api-token" \
    --secret-string file:///tmp/gmail_token.json \
    --tags Key=Project,Value=gmail-inbox-organizer \
    --region $AWS_REGION
```

### 2. Create IAM Role for Lambda

```bash
# Create trust policy
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name GmailOrganizerLambdaRole \
    --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
    --tags Key=Project,Value=gmail-inbox-organizer

# Attach basic Lambda execution policy
aws iam attach-role-policy \
    --role-name GmailOrganizerLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create Secrets Manager access policy
cat > /tmp/secrets-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:gmail-organizer/*"
      ]
    }
  ]
}
EOF

# Create and attach Secrets Manager policy
aws iam create-policy \
    --policy-name GmailOrganizerSecretsAccess \
    --policy-document file:///tmp/secrets-policy.json \
    --tags Key=Project,Value=gmail-inbox-organizer

# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Attach Secrets Manager policy
aws iam attach-role-policy \
    --role-name GmailOrganizerLambdaRole \
    --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/GmailOrganizerSecretsAccess
```

### 3. Create Lambda Deployment Package

```bash
# Create deployment directory
mkdir -p lambda_package

# Install dependencies
pip install --target lambda_package/ \
    google-auth-oauthlib \
    google-auth-httplib2 \
    google-api-python-client \
    openai \
    boto3 \
    python-dotenv

# Copy Lambda handler
cp src/lambda_handler.py lambda_package/

# Create ZIP file
cd lambda_package
zip -r ../gmail-organizer-lambda.zip .
cd ..
```

### 4. Create Lambda Function

```bash
# Get IAM role ARN
ROLE_ARN=$(aws iam get-role --role-name GmailOrganizerLambdaRole --query 'Role.Arn' --output text)

# Create Lambda function
aws lambda create-function \
    --function-name gmail-inbox-organizer \
    --runtime python3.11 \
    --role $ROLE_ARN \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://gmail-organizer-lambda.zip \
    --timeout 900 \
    --memory-size 512 \
    --environment Variables="{AWS_REGION=$AWS_REGION}" \
    --tags Project=gmail-inbox-organizer,Environment=production \
    --region $AWS_REGION
```

### 5. Set Up EventBridge Schedule

```bash
# Create EventBridge rule for daily 9 AM execution (Amsterdam time = 8 AM UTC)
aws events put-rule \
    --name gmail-organizer-daily-9am \
    --description "Trigger Gmail inbox organizer daily at 9 AM Amsterdam time" \
    --schedule-expression "cron(0 8 * * ? *)" \
    --state ENABLED \
    --tags Key=Project,Value=gmail-inbox-organizer \
    --region $AWS_REGION

# Add Lambda permission for EventBridge
aws lambda add-permission \
    --function-name gmail-inbox-organizer \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$AWS_REGION:${AWS_ACCOUNT_ID}:rule/gmail-organizer-daily-9am \
    --region $AWS_REGION

# Add Lambda as EventBridge target
aws events put-targets \
    --rule gmail-organizer-daily-9am \
    --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:${AWS_ACCOUNT_ID}:function:gmail-inbox-organizer" \
    --region $AWS_REGION
```

### 6. Test Lambda Function

```bash
# Invoke Lambda manually
aws lambda invoke \
    --function-name gmail-inbox-organizer \
    --region $AWS_REGION \
    /tmp/lambda-response.json

# View response
cat /tmp/lambda-response.json

# Check CloudWatch Logs
aws logs tail /aws/lambda/gmail-inbox-organizer \
    --since 10m \
    --region $AWS_REGION
```

## Management

### Update Lambda Code

```bash
# Rebuild deployment package
rm -rf lambda_package gmail-organizer-lambda.zip
mkdir lambda_package
pip install --target lambda_package/ -r requirements.txt
cp src/lambda_handler.py lambda_package/
cd lambda_package && zip -r ../gmail-organizer-lambda.zip . && cd ..

# Update Lambda function
aws lambda update-function-code \
    --function-name gmail-inbox-organizer \
    --zip-file fileb://gmail-organizer-lambda.zip \
    --region $AWS_REGION
```

### Update Secrets

```bash
# Update OpenRouter API key
aws secretsmanager update-secret \
    --secret-id "gmail-organizer/openrouter-api-key" \
    --secret-string '{"api_key":"NEW_KEY"}' \
    --region $AWS_REGION

# Update Gmail token (after re-authentication)
aws secretsmanager update-secret \
    --secret-id "gmail-organizer/gmail-api-token" \
    --secret-string file:///tmp/gmail_token.json \
    --region $AWS_REGION
```

### Change Schedule

```bash
# Change to 10 AM Amsterdam time (9 AM UTC)
aws events put-rule \
    --name gmail-organizer-daily-9am \
    --schedule-expression "cron(0 9 * * ? *)" \
    --region $AWS_REGION

# Disable schedule
aws events disable-rule \
    --name gmail-organizer-daily-9am \
    --region $AWS_REGION

# Enable schedule
aws events enable-rule \
    --name gmail-organizer-daily-9am \
    --region $AWS_REGION
```

### View Logs

```bash
# Tail recent logs
aws logs tail /aws/lambda/gmail-inbox-organizer \
    --since 1h \
    --follow \
    --region $AWS_REGION

# Search logs for errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/gmail-inbox-organizer \
    --filter-pattern "ERROR" \
    --region $AWS_REGION
```

## Cost Breakdown

### Monthly Costs (Estimated)

- **Lambda**: $0.003 (30 executions × $0.0001)
- **Secrets Manager**: $1.20 (3 secrets × $0.40)
- **EventBridge**: $0.00 (free tier)
- **CloudWatch Logs**: $0.01
- **Total**: ~$1.25/month

### Cost Optimization

- Use Lambda free tier (1M requests/month)
- Minimize execution time with efficient code
- Use CloudWatch Logs retention policies
- Consider AWS Free Tier eligibility

## Troubleshooting

### Lambda Function Not Running

```bash
# Check function status
aws lambda get-function \
    --function-name gmail-inbox-organizer \
    --region $AWS_REGION

# Check EventBridge rule
aws events describe-rule \
    --name gmail-organizer-daily-9am \
    --region $AWS_REGION
```

### Gmail Token Expired

If the Gmail API token expires, re-authenticate locally and update the secret:

```bash
# Run local script to re-authenticate
python src/gmail_organizer.py

# Convert token to JSON
python3 -c "
import pickle, json
with open('credentials/gmail_token.pickle', 'rb') as f:
    token = pickle.load(f)
token_dict = {
    'token': token.token,
    'refresh_token': token.refresh_token,
    'token_uri': token.token_uri,
    'client_id': token.client_id,
    'client_secret': token.client_secret,
    'scopes': token.scopes
}
with open('/tmp/gmail_token.json', 'w') as f:
    json.dump(token_dict, f)
"

# Update secret
aws secretsmanager update-secret \
    --secret-id "gmail-organizer/gmail-api-token" \
    --secret-string file:///tmp/gmail_token.json \
    --region $AWS_REGION
```

### Insufficient Permissions

Ensure the Lambda IAM role has:
- `AWSLambdaBasicExecutionRole` for CloudWatch Logs
- `secretsmanager:GetSecretValue` for Secrets Manager

## Security Best Practices

- ✅ Use AWS Secrets Manager for all credentials
- ✅ Enable CloudWatch Logs encryption
- ✅ Use least-privilege IAM roles
- ✅ Rotate secrets regularly
- ✅ Monitor CloudWatch Logs for anomalies
- ✅ Enable AWS CloudTrail for audit logging
- ✅ Use VPC for additional network isolation (optional)

## Cleanup

To remove all AWS resources:

```bash
# Delete Lambda function
aws lambda delete-function \
    --function-name gmail-inbox-organizer \
    --region $AWS_REGION

# Delete EventBridge rule
aws events remove-targets \
    --rule gmail-organizer-daily-9am \
    --ids "1" \
    --region $AWS_REGION

aws events delete-rule \
    --name gmail-organizer-daily-9am \
    --region $AWS_REGION

# Delete secrets
aws secretsmanager delete-secret \
    --secret-id "gmail-organizer/openrouter-api-key" \
    --force-delete-without-recovery \
    --region $AWS_REGION

aws secretsmanager delete-secret \
    --secret-id "gmail-organizer/gmail-oauth-credentials" \
    --force-delete-without-recovery \
    --region $AWS_REGION

aws secretsmanager delete-secret \
    --secret-id "gmail-organizer/gmail-api-token" \
    --force-delete-without-recovery \
    --region $AWS_REGION

# Detach and delete IAM policies
aws iam detach-role-policy \
    --role-name GmailOrganizerLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam detach-role-policy \
    --role-name GmailOrganizerLambdaRole \
    --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/GmailOrganizerSecretsAccess

aws iam delete-policy \
    --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/GmailOrganizerSecretsAccess

aws iam delete-role \
    --role-name GmailOrganizerLambdaRole
```
