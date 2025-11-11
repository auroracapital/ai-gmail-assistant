# GitHub Actions CI/CD Setup Guide

This guide will help you set up GitHub Actions workflows for automated testing, code quality checks, and AWS Lambda deployment.

## 📋 Prerequisites

- GitHub repository with admin access
- AWS Lambda function deployed
- OpenRouter API account (for AI categorization)

---

## 🔐 Step 1: Add GitHub Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `OPENROUTER_API_KEY` | OpenRouter API key for Claude Sonnet 4.5 | Get from [OpenRouter Keys](https://openrouter.ai/keys) |
| `AWS_ACCESS_KEY_ID` | AWS access key for Lambda deployment | Create in [AWS IAM Console](https://console.aws.amazon.com/iam/) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Lambda deployment | Created with AWS_ACCESS_KEY_ID |
| `AWS_REGION` | AWS region where Lambda is deployed | Example: `us-east-1`, `eu-west-1` |

### How to Add a Secret:

1. Click "New repository secret"
2. Enter the **Name** (e.g., `OPENROUTER_API_KEY`)
3. Paste your **Value**
4. Click "Add secret"
5. Repeat for all 4 secrets

⚠️ **Security Note**: Never commit real API keys or credentials to your repository. Always use GitHub Secrets or environment variables.

---

## 📁 Step 2: Add Workflow Files

The workflow files should already be in `.github/workflows/`. If not, create them:

### Option A: Push via Git (Recommended)

```bash
git add .github/
git commit -m "feat: Add GitHub Actions CI/CD workflows"
git push origin main
```

### Option B: Manual Upload via GitHub Web UI

1. Go to your repository on GitHub
2. Click "Add file" → "Create new file"
3. Name: `.github/workflows/test.yml`
4. Copy content from the repository
5. Commit the file
6. Repeat for `deploy.yml` and `.github/dependabot.yml`

---

## ✅ Step 3: Verify Setup

Once workflows are pushed and secrets are added:

1. **Check Actions Tab**: Go to the "Actions" tab in your repository
2. You should see workflows running automatically
3. **Test Workflow** will run on every push/PR
4. **Deploy Workflow** will run on push to main

### Manual Trigger (Optional):

You can manually trigger the deployment workflow:

1. Go to Actions → Deploy to AWS Lambda
2. Click "Run workflow"
3. Select branch: `main`
4. Click "Run workflow"

---

## 🔄 What Happens Automatically

### On Every Push/PR:
✅ Code formatting check (Black)  
✅ Linting (flake8)  
✅ Import sorting check (isort)  
✅ Security scanning (safety, bandit)  
✅ Automated tests (pytest)

### On Push to Main:
✅ All tests above  
✅ **Automatic deployment to AWS Lambda**  
✅ Post-deployment testing

### Weekly (Mondays at 9 AM):
✅ Dependabot checks for dependency updates  
✅ Automatic PRs created for updates

---

## 🎯 Workflow Files Overview

### 1. `.github/workflows/test.yml`
**Purpose**: Code quality and testing  
**Triggers**: Push, Pull Request  
**Jobs**:
- `lint`: Black, flake8, isort
- `security`: safety, bandit
- `test`: pytest with coverage

### 2. `.github/workflows/deploy.yml`
**Purpose**: AWS Lambda deployment  
**Triggers**: Push to main, Manual  
**Jobs**:
- Build Lambda package
- Upload to AWS Lambda
- Test deployment

### 3. `.github/dependabot.yml`
**Purpose**: Dependency updates  
**Schedule**: Weekly (Mondays)  
**Updates**:
- Python packages (pip)
- GitHub Actions versions

---

## 🐛 Troubleshooting

### Workflows Not Running?

1. **Check if Actions are enabled**:
   - Go to: Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected

2. **Check if secrets are added**:
   - Go to: Settings → Secrets and variables → Actions
   - Verify all 4 secrets are listed

3. **Check workflow files exist**:
   - Go to repository root
   - Navigate to `.github/workflows/`
   - Verify `test.yml` and `deploy.yml` exist

### Deployment Failing?

1. **Check AWS credentials**:
   - Verify secrets are correctly set in GitHub
   - Test credentials locally: `aws sts get-caller-identity`

2. **Check Lambda function exists**:
   ```bash
   aws lambda get-function --function-name your-function-name --region your-region
   ```

3. **Check CloudWatch Logs**:
   - Go to AWS Console → CloudWatch → Log Groups
   - Find your Lambda function's log group
   - Check recent logs for errors

---

## 📊 Monitoring

### GitHub Actions Dashboard:
Check the "Actions" tab in your repository to monitor workflow runs.

### AWS Lambda Monitoring:
Use AWS CloudWatch to monitor Lambda function execution and errors.

---

## 🎉 Success Criteria

Once setup is complete, you should see:

✅ GitHub Actions tab shows workflows  
✅ Secrets are configured (4 total)  
✅ Test workflow passes on push  
✅ Deploy workflow succeeds on main  
✅ Lambda function updates automatically  
✅ Dependabot creates weekly PRs

---

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review workflow run logs in GitHub Actions tab
3. Check AWS CloudWatch logs for Lambda errors
4. Verify all secrets are correctly configured

---

## 🔒 Security Best Practices

- ✅ Never commit credentials to Git
- ✅ Use GitHub Secrets for all sensitive data
- ✅ Rotate API keys regularly
- ✅ Use least-privilege IAM roles for AWS
- ✅ Enable branch protection rules
- ✅ Require PR reviews before merging
