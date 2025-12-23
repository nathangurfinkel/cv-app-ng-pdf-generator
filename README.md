# CV Builder PDF Service

PDF generation service using Playwright for pixel-perfect CV rendering, designed to run on AWS Fargate.

## Overview

This service handles PDF generation for the CV Builder application:
- Pixel-perfect PDF generation using Playwright
- Multiple CV template support
- Headless browser automation
- Optimized for AWS Fargate deployment

## Architecture

- **Platform**: AWS Fargate (Docker container)
- **Framework**: FastAPI
- **PDF Engine**: Playwright with Chromium
- **Rendering**: Headless browser for pixel-perfect output

## Features

- **Pixel-Perfect Rendering**: Uses Playwright to render the exact same React components the user sees
- **Multiple Templates**: Support for classic, modern, functional, combination, and reverse-chronological templates
- **Scalable**: Runs on AWS Fargate with automatic scaling
- **Cost-Effective**: Only runs when generating PDFs

## Environment Setup

### 1. Create Environment File

```bash
cp env.example .env
```

### 2. Configure Variables

Edit `.env` with your values:

```env
# CORS (set to your frontend domain)
CORS_ORIGINS=http://localhost:5173

# Frontend URL (Playwright needs this to render CVs)
FRONTEND_URL=http://localhost:5173

# Debug
DEBUG=false
VERBOSE=false
```

> **For production:**
> - Set `CORS_ORIGINS` and `FRONTEND_URL` to your Amplify domain
> - Example: `https://d1z0zksl0bfdg3.amplifyapp.com`

### 3. Never Commit Secrets

⚠️ `.env` is git-ignored. Never commit environment files.

## Local Development

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Playwright browsers**:
```bash
playwright install chromium
```

3. **Set up environment** (see above)

4. **Run locally**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Test the service**:
```bash
# Health check
curl http://localhost:8000/health

# List templates
curl http://localhost:8000/pdf/templates
```

## Docker Development

1. Build the Docker image:
```bash
docker build -t cv-pdf-service .
```

2. Run the container:
```bash
docker run -p 8000:8000 -e FRONTEND_URL=http://localhost:5173 cv-pdf-service
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `GET /pdf/templates` - Get available PDF templates
- `POST /pdf/generate` - Generate PDF from CV data

## PDF Generation Workflow

1. Frontend sends CV data and template preference to `/pdf/generate`
2. Service generates a unique ID for the request
3. Service navigates to the frontend's print page with the unique ID
4. Frontend renders the CV using the same React components
5. Playwright captures the rendered page as a PDF
6. PDF is returned to the frontend for download

## Request Format

```json
{
  "cv_data": {
    "personal": { ... },
    "experience": [ ... ],
    "education": [ ... ],
    "skills": { ... }
  },
  "template": "classic",
  "frontend_url": "https://your-amplify-app.com"
}
```

## Response Format

Returns a PDF file with appropriate headers for download.

## Deployment to AWS Fargate

### Automated Deployment (Recommended)

Use the provided deployment script:

```bash
./deploy.sh
```

This script will:
- Automatically detect your AWS account ID
- Build Docker image
- Push to ECR
- Register/update ECS task definition
- Create/update Fargate service

### Set Up Load Balancer (Optional but Recommended)

For a stable endpoint that doesn't change when tasks restart:

```bash
./setup-alb.sh
```

This creates an Application Load Balancer with:
- Stable DNS name
- Health checks
- Auto-scaling support

### Manual Deployment

1. **Build and push to ECR**:
```bash
# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Build image
docker build -t cv-pdf-service .

# Tag for ECR
docker tag cv-pdf-service:latest \
  $ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/cv-pdf-service:latest

# Login to ECR
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  $ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com

# Push image
docker push $ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/cv-pdf-service:latest
```

2. **Register task definition**:
```bash
# The task-definition.json.template uses ACCOUNT_ID placeholder
# Replace it and register
cat task-definition.json.template | \
  sed "s/ACCOUNT_ID/$ACCOUNT_ID/g" | \
  aws ecs register-task-definition \
    --cli-input-json file:///dev/stdin \
    --region eu-north-1
```

> **Note**: The `task-definition.json.template` file contains placeholders (`ACCOUNT_ID`) that must be replaced before registration. The `deploy.sh` script automatically handles this replacement with the actual AWS account ID. **DO NOT** manually edit the template with your account ID - it will be handled by the deployment script.

3. **Create or update service**:
```bash
aws ecs update-service \
  --cluster cv-builder-cluster \
  --service cv-pdf-service \
  --force-new-deployment \
  --region eu-north-1
```

## Infrastructure

### AWS Resources

#### Account Information
- **Account ID**: Retrieved via AWS CLI (`aws sts get-caller-identity`)
- **Region**: `eu-north-1` (Stockholm)

#### ECS/Fargate
- **Cluster**: cv-builder-cluster
- **Service**: cv-pdf-service
- **Task Definition**: cv-pdf-service
- **Launch Type**: FARGATE
- **Desired Count**: 1

#### Task Configuration
- **CPU**: 512 (.5 vCPU)
- **Memory**: 1024 MB (1 GB)
- **Network Mode**: awsvpc
- **Platform Version**: LATEST

#### Container
- **Name**: cv-pdf-service
- **Image**: ECR repository
- **Port**: 8000
- **Essential**: true

### Network Configuration

#### VPC
- **VPC ID**: Retrieved from subnet
- **Subnets**: 3 subnets across availability zones
  - eu-north-1a
  - eu-north-1b
  - eu-north-1c

#### Security Group
- **Ingress**: Port 8000 (HTTP)
- **Egress**: All traffic (for internet access)

#### Public IP
- **Enabled**: Yes (required for Playwright to access frontend)
- **Type**: Dynamic (changes on task restart)

### Service Endpoints

#### Current Access
- **Dynamic IP**: Retrieved via AWS CLI
- **Port**: 8000
- **Protocol**: HTTP
- **Example**: `http://51.20.134.127:8000`

#### Application Load Balancer (Recommended)
- **Stable Endpoint**: ALB DNS name
- **Target Group**: cv-pdf-tg
- **Health Check**: `/health`
- **Benefits**: Stable URL, auto-scaling, SSL termination

### Environment Variables

#### Required for Container
Set these in task definition or deployment scripts:

```bash
# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.com

# Frontend URL (for Playwright to render CV)
FRONTEND_URL=https://your-amplify-app.com

# Debug Configuration
DEBUG=false
VERBOSE=false
```

### ECR Repository

#### Repository Details
- **Name**: cv-pdf-service
- **URI**: `<account-id>.dkr.ecr.eu-north-1.amazonaws.com/cv-pdf-service`

### IAM Roles

#### Task Execution Role
Permissions for ECS to pull images and write logs:
- `AmazonECSTaskExecutionRolePolicy`
- `AmazonEC2ContainerRegistryReadOnly`

#### Task Role
Permissions for the container itself (if needed):
- Custom policies for AWS service access

### Dependencies
- **Playwright**: Headless browser automation
- **Chromium**: Browser engine (bundled)
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server

## Application Load Balancer Setup

### Creating ALB

```bash
# Run setup script
./setup-alb.sh
```

This creates:
- Application Load Balancer
- Target Group (IP targets)
- Listener (HTTP:80)
- Security Groups
- Health checks

### Benefits
- **Stable endpoint**: DNS name doesn't change
- **Auto-scaling**: Add more tasks as needed
- **Health checks**: Automatic unhealthy task replacement
- **SSL/TLS**: Easy certificate management

## Monitoring

### CloudWatch Logs
- **Log Group**: `/ecs/cv-pdf-service`
- **Retention**: 7 days (configurable)
- **Streams**: One per task

### CloudWatch Metrics

**ECS Service Metrics**:
- CPUUtilization
- MemoryUtilization
- RunningTaskCount
  
**Task Metrics**:
- CPU and memory per task
- Network I/O

### Container Insights
- Enable for detailed container metrics
- Additional cost for metric storage

## Troubleshooting

### Service Won't Start
1. Check CloudWatch logs for errors
2. Verify task definition is valid
3. Check security group allows port 8000
4. Verify ECR image exists and is accessible

### PDF Generation Fails
1. Check frontend URL is accessible from container
2. Verify Playwright is installed correctly
3. Check memory/CPU limits aren't too low
4. Review CloudWatch logs for Chromium errors

### Connection Timeouts
1. Verify public IP is assigned
2. Check security group rules
3. Verify frontend CORS allows requests
4. Check network ACLs

### Out of Memory
1. Increase task memory allocation
2. Optimize Chromium launch options
3. Review memory leaks in code
4. Consider PDF size limits

## Performance Optimization

### Task Resources
- **CPU**: 512 units minimum for Chromium
- **Memory**: 1024 MB minimum for Playwright
- Scale up if PDFs are complex

### Chromium Options
```python
args=[
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',  # Important for limited memory
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--disable-gpu'
]
```

### Scaling
- Increase desired count for higher throughput
- ALB distributes load across tasks
- Auto-scaling based on CPU/memory

## Cost Management

### Fargate Pricing
- Pay per vCPU-hour and GB-hour
- Current: 0.5 vCPU × 1 GB = ~$15/month (24/7)
- Optimize by stopping service when not needed

### ECR Storage
- Pay per GB stored per month
- Delete old images regularly

### Data Transfer
- Outbound data transfer costs
- Minimize by optimizing PDF sizes

## Security Best Practices

### Container Security
- Use minimal base image
- Scan images for vulnerabilities
- Update dependencies regularly

### Network Security
- Restrict security group ingress
- Use private subnets with NAT (optional)
- Enable VPC Flow Logs

### CORS
- Restrict origins to frontend domain only
- Validate all inputs
- Sanitize file paths

### Secrets Management

PDF service doesn't require API keys or sensitive credentials currently.

If secrets are needed in the future, use AWS Secrets Manager or SSM Parameter Store:
```json
{
  "secrets": [
    {
      "name": "SECRET_NAME",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
    }
  ]
}
```

## Additional Resources

- [AWS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Playwright Documentation](https://playwright.dev/python/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
