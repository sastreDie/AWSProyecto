# Screenshot Management System

> A serverless AWS application for managing, filtering, and serving gaming screenshots with automated content moderation.

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3%20%7C%20DynamoDB-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Usage](#usage)
- [Cost Estimation](#cost-estimation)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Documentation](#documentation)

---

## 🎯 Overview

This system provides a complete serverless solution for managing gaming screenshots with:

- **Automated uploads** via REST API
- **Content moderation** using text filtering and optional AWS Rekognition
- **Secure storage** in S3 with encryption
- **Fast retrieval** with pre-signed URLs
- **User authentication** via AWS Cognito
- **VPC isolation** for enhanced security
- **CI/CD pipeline** for automated deployments

**Use Cases:**
- Gaming communities sharing screenshots
- Content moderation platforms
- Image hosting services
- Gaming achievement systems

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────┐
│  User   │
└────┬────┘
     │
     ▼
┌─────────────────┐      ┌──────────────┐
│  API Gateway    │◄────►│   Cognito    │
│  + CloudFront   │      │  User Pool   │
└────┬────────────┘      └──────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                │
│  ┌──────────────────────────────────────────────┐  │
│  │         Private Subnet (10.0.1.0/24)         │  │
│  │                                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Image   │  │Profanity │  │  Image   │  │  │
│  │  │ Uploader │  │  Filter  │  │Retrieval │  │  │
│  │  │  Lambda  │  │  Lambda  │  │  Lambda  │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  │  │
│  │       │             │             │         │  │
│  │       │    ┌────────┴────────┐    │         │  │
│  │       │    │   VPC Endpoints │    │         │  │
│  │       │    │  S3 | DynamoDB  │    │         │  │
│  │       │    └────────┬────────┘    │         │  │
│  └───────┼─────────────┼─────────────┼─────────┘  │
└──────────┼─────────────┼─────────────┼────────────┘
           │             │             │
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ S3 Raw   │  │ DynamoDB │  │S3 Process│
    │ Bucket   │  │  Table   │  │  Bucket  │
    └──────────┘  └──────────┘  └──────────┘
           │             │             │
           └─────────────┴─────────────┘
                       │
                       ▼
                ┌──────────────┐
                │  SNS Topics  │
                │  + KMS Key   │
                └──────────────┘
```

### Data Flow

1. **Upload Flow:**
   ```
   User → API Gateway → Image Uploader Lambda → S3 Raw → SNS Topic
   → Profanity Filter Lambda → S3 Processed → DynamoDB
   ```

2. **Retrieval Flow:**
   ```
   User → API Gateway → Image Retrieval Lambda → DynamoDB + S3
   → Pre-signed URLs → User
   ```

3. **Content Moderation:**
   ```
   SNS Trigger → Profanity Filter → Text Analysis + Rekognition (optional)
   → APPROVED/REJECTED → Update DynamoDB → Notify User
   ```

---

## ✨ Features

### Core Features
- ✅ **RESTful API** - Upload and retrieve screenshots
- ✅ **Content Filtering** - Automated profanity detection
- ✅ **User Authentication** - Cognito-based JWT authentication
- ✅ **Secure Storage** - Encrypted S3 buckets with KMS
- ✅ **VPC Isolation** - Lambda functions in private subnets
- ✅ **Pre-signed URLs** - Temporary secure access to images
- ✅ **Metadata Storage** - DynamoDB for fast queries

### Advanced Features
- 🔄 **CI/CD Pipeline** - Automated deployments via CodePipeline
- 📊 **CloudWatch Monitoring** - Logs and metrics
- 🔐 **IAM Least Privilege** - Separate roles per Lambda
- 🌐 **CloudFront CDN** - Global content delivery (optional)
- 🤖 **AWS Rekognition** - AI-powered image moderation (optional)
- 📧 **SNS Notifications** - User notifications on processing

---

## 🛠️ Tech Stack

### AWS Services
| Service | Purpose |
|---------|---------|
| **Lambda** | Serverless compute for business logic |
| **S3** | Object storage for images |
| **DynamoDB** | NoSQL database for metadata |
| **API Gateway** | REST API endpoint |
| **Cognito** | User authentication |
| **SNS** | Asynchronous messaging |
| **VPC** | Network isolation |
| **KMS** | Encryption key management |
| **CloudWatch** | Logging and monitoring |
| **CloudFront** | CDN (optional) |
| **Rekognition** | Image analysis (optional) |
| **CodePipeline** | CI/CD automation |
| **CodeBuild** | Build automation |

### Languages & Tools
- **Python 3.12** - Lambda runtime
- **CloudFormation** - Infrastructure as Code
- **Boto3** - AWS SDK for Python
- **PowerShell** - Testing scripts
- **Git** - Version control

---

## 📦 Prerequisites

### Required
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Git installed
- Python 3.12+ (for local testing)

### Permissions Needed
- CloudFormation: Full access
- Lambda: Create/update functions
- S3: Create buckets, upload objects
- DynamoDB: Create tables
- IAM: Create roles (or coordinate with security team)
- VPC: Create VPC resources (EC2 permissions)
- KMS: Create/use encryption keys

### Optional
- GitHub account (for CI/CD pipeline)
- draw.io (for viewing architecture diagram)

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/sastreDie/AWSProyecto.git
cd AWSProyecto
```

### 2. Deploy IAM Roles

**Option A: Via AWS Console**
1. Go to CloudFormation console
2. Create stack → Upload `iac/iam-stack.yaml`
3. Stack name: `screenshot-system-iam`
4. Check "I acknowledge that AWS CloudFormation might create IAM resources"
5. Create stack

**Option B: Via AWS CLI**
```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-iam \
  --template-body file://iac/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### 3. Deploy Network Stack (VPC)

```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-network \
  --template-body file://iac/network-stack.yaml
```

### 4. Package Lambda Functions

**Windows:**
```cmd
scripts\package-lambdas.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/package-lambdas.sh
./scripts/package-lambdas.sh
```

### 5. Upload Lambda Packages to S3

```bash
# Create deployment bucket
aws s3 mb s3://screenshot-system-lambda-deployment-YOUR-ACCOUNT-ID

# Upload packages
aws s3 cp dist/lambda/ s3://screenshot-system-lambda-deployment-YOUR-ACCOUNT-ID/lambda/ --recursive
```

### 6. Deploy Infrastructure Stack

```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-infra \
  --template-body file://iac/infrastructure-stack.yaml \
  --parameters \
    ParameterKey=ImageUploaderCodeBucket,ParameterValue=screenshot-system-lambda-deployment-YOUR-ACCOUNT-ID \
  --capabilities CAPABILITY_IAM
```

### 7. Get API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

---

## 📚 Deployment

For detailed deployment instructions, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Step-by-step deployment guide
- [DEPLOYMENT_VPC.md](DEPLOYMENT_VPC.md) - VPC-specific deployment
- [PIPELINE_SETUP.md](PIPELINE_SETUP.md) - CI/CD pipeline setup
- [SECURITY_REQUEST.md](SECURITY_REQUEST.md) - IAM permissions guide

### Deployment Order

1. **IAM Stack** - Create roles first
2. **Network Stack** - Set up VPC (if using VPC isolation)
3. **Infrastructure Stack** - Deploy all application resources
4. **Pipeline Stack** (optional) - Set up CI/CD

---

## 💻 Usage

### Create a User

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --password MyPassword123! \
  --permanent
```

### Authenticate

```bash
# Get Client ID
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name screenshot-system-infra \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
  --output text)

# Get ID Token
aws cognito-idp admin-initiate-auth \
  --user-pool-id $USER_POOL_ID \
  --client-id $CLIENT_ID \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=MyPassword123!
```

### Upload Screenshot

```bash
# Using curl (small images only, <10MB)
curl -X POST https://YOUR-API-ENDPOINT/upload \
  -H "Authorization: YOUR-ID-TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "BASE64_ENCODED_IMAGE",
    "filename": "screenshot.png",
    "game_title": "My Game",
    "description": "Epic moment!"
  }'
```

**For larger images, use the PowerShell test scripts:**
```powershell
# Edit test-real-image.ps1 with your values
.\test-real-image.ps1
```

### Retrieve Screenshots

```bash
curl -X GET https://YOUR-API-ENDPOINT/screenshots \
  -H "Authorization: YOUR-ID-TOKEN"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a screenshot |
| GET | `/screenshots` | Retrieve user's screenshots |
| GET | `/screenshots?status=APPROVED` | Filter by status |
| GET | `/screenshots?limit=10` | Limit results |

---

## 💰 Cost Estimation

### Monthly Cost Breakdown

**Scenario: 1,000 screenshots/month, 100 active users**

| Service | Cost/Month |
|---------|------------|
| Lambda | $0.15 |
| S3 Storage | $0.61 |
| DynamoDB | $0.03 |
| API Gateway | $1.10 |
| VPC (NAT + Endpoints) | $48.35 |
| KMS | $1.03 |
| CloudWatch | $0.56 |
| **Total** | **~$52/month** |

**Cost Optimization:**
- Remove NAT Gateway: Save $33/month (use VPC Endpoints only)
- Remove VPC: Save $48/month (less secure)
- Disable Rekognition: Save $1-20/month

**Detailed breakdown:** See [COST_ESTIMATION.md](COST_ESTIMATION.md)

---

## 🔒 Security

### Implemented Security Measures

- ✅ **VPC Isolation** - Lambdas in private subnets
- ✅ **Encryption at Rest** - S3 and DynamoDB encrypted with KMS
- ✅ **Encryption in Transit** - HTTPS only
- ✅ **IAM Least Privilege** - Minimal permissions per role
- ✅ **Authentication** - Cognito JWT tokens
- ✅ **Private S3 Buckets** - No public access
- ✅ **Pre-signed URLs** - Temporary access (1 hour expiry)
- ✅ **Content Filtering** - Automated profanity detection
- ✅ **Security Groups** - Network-level access control
- ✅ **CloudWatch Logs** - Audit trail

### Security Best Practices

1. **Rotate KMS keys** annually
2. **Enable MFA** for Cognito users
3. **Set up CloudTrail** for API auditing
4. **Configure WAF** on API Gateway (optional)
5. **Regular security audits** of IAM policies
6. **Monitor CloudWatch** for suspicious activity

---

## 📊 Monitoring

### CloudWatch Dashboards

Key metrics to monitor:
- Lambda invocations and errors
- API Gateway 4xx/5xx errors
- DynamoDB throttling
- S3 bucket size
- VPC flow logs

### Recommended Alarms

```bash
# Lambda errors > 5%
aws cloudwatch put-metric-alarm \
  --alarm-name screenshot-lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name screenshot-api-errors \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### Logging

View Lambda logs:
```bash
aws logs tail /aws/lambda/screenshot-system-image-uploader --follow
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Access Denied" Error
**Cause:** Missing IAM permissions  
**Solution:** Check IAM roles have correct policies attached

#### 2. "Request Too Large" (413)
**Cause:** Image exceeds API Gateway 10MB limit  
**Solution:** Implement pre-signed URL upload flow (see `upload-image-v2.ps1`)

#### 3. Lambda Timeout
**Cause:** VPC networking issues or slow S3/DynamoDB  
**Solution:** 
- Check VPC endpoints are configured
- Increase Lambda timeout
- Check NAT Gateway is working

#### 4. KMS Decrypt Error
**Cause:** Lambda role missing KMS permissions  
**Solution:** Add `kms:Decrypt` and `kms:GenerateDataKey` to Lambda role

#### 5. "Unauthorized" from API
**Cause:** Invalid or expired Cognito token  
**Solution:** Re-authenticate to get new token

### Debug Commands

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name screenshot-system-infra

# View Lambda logs
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Test Lambda directly
aws lambda invoke \
  --function-name screenshot-system-image-uploader \
  --payload '{"test": true}' \
  response.json

# Check DynamoDB items
aws dynamodb scan --table-name screenshot-system-metadata --limit 5
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repo
git clone https://github.com/sastreDie/AWSProyecto.git
cd AWSProyecto

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run local tests
python -m pytest tests/
```

---

## 📖 Documentation

### Core Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [COST_ESTIMATION.md](COST_ESTIMATION.md) - Cost analysis
- [SECURITY_REQUEST.md](SECURITY_REQUEST.md) - IAM permissions

### Additional Resources
- [DEPLOYMENT_VPC.md](DEPLOYMENT_VPC.md) - VPC deployment
- [PIPELINE_SETUP.md](PIPELINE_SETUP.md) - CI/CD setup
- [architecture-diagram.drawio](architecture-diagram.drawio) - Visual diagram

### CloudFormation Templates
- `iac/iam-stack.yaml` - IAM roles and policies
- `iac/network-stack.yaml` - VPC and networking
- `iac/infrastructure-stack.yaml` - Main application resources
- `iac/pipeline-stack.yaml` - CI/CD pipeline

### Lambda Functions
- `src/lambda/image_uploader.py` - Upload handler
- `src/lambda/profanity_filter.py` - Content moderation
- `src/lambda/image_retrieval.py` - Retrieval handler

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Diego Sastre** - *Initial work* - [sastreDie](https://github.com/sastreDie)

---

## 🙏 Acknowledgments

- AWS Documentation and best practices
- Celula 5 team for requirements and testing
- Open source community for tools and libraries

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review CloudWatch logs for errors

---

## 🗺️ Roadmap

### Planned Features
- [ ] Thumbnail generation
- [ ] Multi-resolution image support
- [ ] Advanced search and filtering
- [ ] Social features (likes, comments)
- [ ] Mobile app integration
- [ ] Real-time notifications via WebSocket
- [ ] Image compression and optimization
- [ ] Batch upload support

### Optimizations
- [ ] CloudFront CDN integration
- [ ] DynamoDB DAX caching
- [ ] S3 Transfer Acceleration
- [ ] Lambda@Edge for global performance
- [ ] Reserved capacity for cost savings

---

## 📊 Project Stats

- **Lines of Code:** ~2,000
- **AWS Services Used:** 11
- **Lambda Functions:** 3
- **CloudFormation Templates:** 4
- **Estimated Monthly Cost:** $5-50 (depending on usage)

---

**Built with ❤️ using AWS Serverless**
