# CI/CD Pipeline Setup Guide

## Overview

This pipeline automates deployment across three AWS accounts:
- **Construccion (Build)** - Where the pipeline runs
- **Dry-run** - Testing environment
- **Production** - Live environment

## Architecture

```
GitHub → CodePipeline → CodeBuild → Deploy to Dry-run → Manual Approval → Deploy to Production
```

## Prerequisites

### 1. GitHub Setup
- Repository with your code
- GitHub Personal Access Token with `repo` and `admin:repo_hook` permissions
- Create token at: https://github.com/settings/tokens

### 2. AWS Accounts
You need three AWS account IDs:
- Construction account (where pipeline runs)
- Dry-run account
- Production account

### 3. Cross-Account Roles (for Dry-run and Production accounts)

If deploying to different accounts, create this role in each:

```yaml
# Run this in Dry-run and Production accounts
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  CrossAccountRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: screenshot-system-cross-account-role
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: arn:aws:iam::<CONSTRUCTION_ACCOUNT_ID>:root
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/PowerUserAccess
```

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
cd AWSproyecto
git init
git add .
git commit -m "Initial commit with CI/CD pipeline"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Deploy Pipeline Stack

```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-pipeline \
  --template-body file://iac/pipeline-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=screenshot-system \
    ParameterKey=GitHubRepo,ParameterValue=YOUR_USERNAME/YOUR_REPO \
    ParameterKey=GitHubBranch,ParameterValue=main \
    ParameterKey=GitHubToken,ParameterValue=YOUR_GITHUB_TOKEN \
    ParameterKey=DryRunAccountId,ParameterValue=123456789012 \
    ParameterKey=ProductionAccountId,ParameterValue=987654321098 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Step 3: Wait for Pipeline Creation

```bash
aws cloudformation wait stack-create-complete \
  --stack-name screenshot-system-pipeline
```

### Step 4: Get Pipeline URL

```bash
aws cloudformation describe-stacks \
  --stack-name screenshot-system-pipeline \
  --query 'Stacks[0].Outputs[?OutputKey==`PipelineUrl`].OutputValue' \
  --output text
```

## Pipeline Stages

### 1. Source
- Triggered automatically on push to `main` branch
- Pulls code from GitHub

### 2. Build
- Packages Lambda functions into zip files
- Uploads to S3 Lambda bucket
- Uploads CloudFormation templates

### 3. Deploy to Dry-Run
- Deploys IAM stack first
- Then deploys infrastructure stack
- Creates all resources in dry-run environment

### 4. Manual Approval
- Pipeline pauses here
- Review dry-run deployment
- Approve or reject in AWS Console

### 5. Deploy to Production
- Same as dry-run
- Only runs after approval

## Testing the Pipeline

### Trigger a Deployment

```bash
# Make a change
echo "# Test change" >> README.md
git add README.md
git commit -m "Test pipeline trigger"
git push origin main
```

### Monitor Pipeline

```bash
# Watch pipeline status
aws codepipeline get-pipeline-state \
  --name screenshot-system-pipeline
```

### View Build Logs

```bash
# Get latest build ID
BUILD_ID=$(aws codebuild list-builds-for-project \
  --project-name screenshot-system-build \
  --query 'ids[0]' --output text)

# View logs
aws codebuild batch-get-builds \
  --ids $BUILD_ID \
  --query 'builds[0].logs.deepLink' \
  --output text
```

## Troubleshooting

### Pipeline Fails at Source Stage
- Check GitHub token is valid
- Verify repository name is correct
- Ensure webhook is registered

### Build Stage Fails
- Check CodeBuild logs in CloudWatch
- Verify buildspec.yml syntax
- Ensure Lambda code has no syntax errors

### Deploy Stage Fails
- Check CloudFormation events
- Verify IAM permissions
- Check if resources already exist

### Cross-Account Deployment Fails
- Verify cross-account role exists
- Check trust relationship allows construction account
- Ensure role has sufficient permissions

## Cost Optimization

- Pipeline artifacts deleted after 30 days
- CodeBuild uses small instance (BUILD_GENERAL1_SMALL)
- S3 versioning enabled but with lifecycle rules

## Security Best Practices

- GitHub token stored as NoEcho parameter
- All S3 buckets have public access blocked
- IAM roles follow least privilege
- Cross-account access uses AssumeRole

## Cleanup

To delete everything:

```bash
# Delete pipeline stack
aws cloudformation delete-stack --stack-name screenshot-system-pipeline

# Delete dry-run stacks
aws cloudformation delete-stack --stack-name screenshot-system-infra-dryrun
aws cloudformation delete-stack --stack-name screenshot-system-iam-dryrun

# Delete production stacks
aws cloudformation delete-stack --stack-name screenshot-system-infra-prod
aws cloudformation delete-stack --stack-name screenshot-system-iam-prod

# Empty and delete S3 buckets manually
```

## Next Steps

1. Add automated tests in build stage
2. Add notifications (SNS/Slack) for pipeline events
3. Implement blue/green deployments
4. Add rollback capabilities
5. Set up CloudWatch dashboards for monitoring
