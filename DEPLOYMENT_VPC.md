# Deployment Guide with VPC and Security

## Overview

This deployment includes full VPC isolation, encryption, and network firewall inspection as required by the security team.

## Architecture Components

### Network Layer (network-stack.yaml)
- VPC with private subnets (2 AZs for HA)
- VPC Endpoints (Gateway): S3, DynamoDB
- VPC Endpoints (Interface): CloudWatch Logs, SNS, Rekognition, KMS
- Network Firewall for traffic inspection
- VPC Flow Logs
- Security Groups

### IAM Layer (iam-stack.yaml)
- Lambda execution roles with VPC permissions
- KMS encryption permissions
- Least privilege access

### Infrastructure Layer (infrastructure-stack.yaml)
- KMS key for encryption
- S3 buckets with KMS encryption
- DynamoDB with KMS encryption
- Lambda functions in VPC
- SNS topics with KMS encryption
- API Gateway with Cognito
- CloudFront distribution

## Deployment Order

### Step 1: Deploy Network Stack

```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-network \
  --template-body file://iac/network-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=screenshot-system \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Wait for completion (takes ~10 minutes due to Network Firewall)
aws cloudformation wait stack-create-complete \
  --stack-name screenshot-system-network
```

**What this creates:**
- VPC (10.0.0.0/16)
- 2 Private Subnets (10.0.1.0/24, 10.0.2.0/24)
- 1 Firewall Subnet (10.0.10.0/24)
- 6 VPC Endpoints (S3, DynamoDB, Logs, SNS, Rekognition, KMS)
- Network Firewall with stateful rules
- Security Groups for Lambda and VPC Endpoints
- VPC Flow Logs

### Step 2: Deploy IAM Stack

```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-iam \
  --template-body file://iac/iam-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=screenshot-system \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name screenshot-system-iam
```

**What this creates:**
- ImageUploaderRole (with VPC and KMS permissions)
- ProfanityFilterRole (with VPC, KMS, and Rekognition permissions)
- ImageRetrievalRole (with VPC and KMS permissions)
- ApiGatewayRole

### Step 3: Package and Upload Lambda Functions

```bash
# Create deployment bucket (if not exists)
aws s3 mb s3://screenshot-system-lambda-code-$(aws sts get-caller-identity --query Account --output text)

# Package Lambda functions
cd src/lambda
zip -r ../../dist/image_uploader.zip image_uploader.py
zip -r ../../dist/profanity_filter.zip profanity_filter.py
zip -r ../../dist/image_retrieval.zip image_retrieval.py
cd ../..

# Upload to S3
aws s3 cp dist/image_uploader.zip s3://screenshot-system-lambda-code-$(aws sts get-caller-identity --query Account --output text)/lambda/
aws s3 cp dist/profanity_filter.zip s3://screenshot-system-lambda-code-$(aws sts get-caller-identity --query Account --output text)/lambda/
aws s3 cp dist/image_retrieval.zip s3://screenshot-system-lambda-code-$(aws sts get-caller-identity --query Account --output text)/lambda/
```

### Step 4: Deploy Infrastructure Stack

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws cloudformation create-stack \
  --stack-name screenshot-system-infra \
  --template-body file://iac/infrastructure-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=screenshot-system \
    ParameterKey=ImageUploaderCodeBucket,ParameterValue=screenshot-system-lambda-code-${ACCOUNT_ID} \
    ParameterKey=ImageUploaderCodeKey,ParameterValue=lambda/image_uploader.zip \
    ParameterKey=ProfanityFilterCodeKey,ParameterValue=lambda/profanity_filter.zip \
    ParameterKey=ImageRetrievalCodeKey,ParameterValue=lambda/image_retrieval.zip \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for completion (takes ~5 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name screenshot-system-infra
```

**What this creates:**
- KMS encryption key
- S3 buckets (raw and processed) with KMS encryption
- DynamoDB table with KMS encryption
- 3 Lambda functions in VPC
- SNS topics with KMS encryption
- API Gateway with Cognito
- CloudFront distribution

### Step 5: Get Outputs

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Get Cognito User Pool ID
aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Get CloudFront domain
aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomain`].OutputValue' \
  --output text
```

## Security Features Implemented

### ✅ VPC Isolation
- All Lambda functions run in private subnets
- No internet gateway (no direct internet access)
- All AWS service access via VPC Endpoints

### ✅ Encryption at Rest
- S3 buckets: KMS encryption
- DynamoDB: KMS encryption
- SNS topics: KMS encryption
- CloudWatch Logs: Default encryption

### ✅ Encryption in Transit
- API Gateway: HTTPS only
- CloudFront: HTTPS redirect
- VPC Endpoints: TLS 1.2+

### ✅ Network Inspection
- Network Firewall inspects all traffic
- Stateful rules block malicious domains
- Flow logs capture all network activity

### ✅ IAM Least Privilege
- Each Lambda has minimal required permissions
- VPC execution role for ENI management
- KMS permissions scoped to specific keys

## Verification

### Check VPC Configuration

```bash
# Verify Lambda is in VPC
aws lambda get-function-configuration \
  --function-name screenshot-system-profanity-filter \
  --query 'VpcConfig'

# Should show SubnetIds and SecurityGroupIds
```

### Check Encryption

```bash
# Verify S3 encryption
aws s3api get-bucket-encryption \
  --bucket screenshot-system-raw-screenshots

# Verify DynamoDB encryption
aws dynamodb describe-table \
  --table-name screenshot-system-metadata \
  --query 'Table.SSEDescription'
```

### Check Network Firewall

```bash
# Get firewall status
aws network-firewall describe-firewall \
  --firewall-name screenshot-system-firewall \
  --query 'Firewall.FirewallStatus'
```

### Check VPC Endpoints

```bash
# List VPC endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(aws cloudformation describe-stacks --stack-name screenshot-system-network --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' --output text)"
```

## Testing

### Test Lambda in VPC

```bash
# Invoke Lambda (should work via VPC endpoints)
aws lambda invoke \
  --function-name screenshot-system-profanity-filter \
  --payload '{"Records":[{"Sns":{"Message":"{\"screenshot_id\":\"test\",\"user_id\":\"user1\",\"s3_key\":\"raw/test.png\",\"bucket\":\"screenshot-system-raw-screenshots\"}"}}]}' \
  response.json

# Check CloudWatch Logs (via VPC endpoint)
aws logs tail /aws/lambda/screenshot-system-profanity-filter --follow
```

## Troubleshooting

### Lambda Timeout in VPC

**Problem:** Lambda times out when accessing AWS services

**Solution:** Verify VPC endpoints are created and associated with route table

```bash
# Check VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC_ID>"

# Check route table associations
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<VPC_ID>"
```

### KMS Access Denied

**Problem:** Lambda can't decrypt S3 objects or DynamoDB items

**Solution:** Verify Lambda role has KMS permissions

```bash
# Check Lambda role policies
aws iam get-role-policy \
  --role-name screenshot-system-profanity-filter-role \
  --policy-name ProfanityFilterPolicy
```

### Network Firewall Blocking Traffic

**Problem:** Legitimate traffic is blocked

**Solution:** Check firewall logs and adjust rules

```bash
# View firewall logs
aws logs tail /aws/networkfirewall/screenshot-system --follow
```

## Cost Estimates

### Network Layer
- VPC: Free
- VPC Endpoints (Interface): ~$7.20/month each × 4 = $28.80/month
- VPC Endpoints (Gateway): Free
- Network Firewall: ~$0.395/hour = $285/month
- VPC Flow Logs: ~$0.50/GB ingested

### Encryption
- KMS: $1/month per key + $0.03 per 10,000 requests

### Total Additional Cost for Security
- **~$315/month** (mostly Network Firewall)

**Note:** Network Firewall is expensive. For dev/test, you can remove it and just use VPC + endpoints.

## Cleanup

```bash
# Delete in reverse order
aws cloudformation delete-stack --stack-name screenshot-system-infra
aws cloudformation delete-stack --stack-name screenshot-system-iam
aws cloudformation delete-stack --stack-name screenshot-system-network

# Empty S3 buckets first
aws s3 rm s3://screenshot-system-raw-screenshots --recursive
aws s3 rm s3://screenshot-system-processed-screenshots --recursive
aws s3 rb s3://screenshot-system-raw-screenshots
aws s3 rb s3://screenshot-system-processed-screenshots
```

## Next Steps

1. Create Cognito users for testing
2. Test API endpoints with curl
3. Upload test screenshots
4. Verify Rekognition analysis
5. Check CloudWatch metrics and logs
6. Set up CloudWatch alarms
7. Deploy CI/CD pipeline
