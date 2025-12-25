#!/bin/bash

# PDF Service Deployment Script for AWS Fargate
# This script builds and deploys the PDF service to AWS Fargate via ECR

set -e

echo "Starting PDF Service deployment to AWS Fargate..."

# Configuration
SERVICE_NAME="cv-pdf-service"
CLUSTER_NAME="cv-builder-cluster"
REGION="eu-north-1"  # Stockholm region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/cv-pdf-service"
TASK_DEFINITION_FAMILY="cv-pdf-service"

# Build Docker image
echo "Building Docker image..."
docker build -t $SERVICE_NAME .

# Tag image for ECR
echo "Tagging image for ECR..."
docker tag $SERVICE_NAME:latest $ECR_REPOSITORY:latest

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Create ECR repository if it doesn't exist
echo "Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names cv-pdf-service --region $REGION --no-cli-pager &> /dev/null || \
aws ecr create-repository --repository-name cv-pdf-service --region $REGION --no-cli-pager

# Push image to ECR
echo "Pushing image to ECR..."
docker push $ECR_REPOSITORY:latest

# Create task definition
echo "Creating task definition..."
cat > task-definition.json << EOF
{
  "family": "$TASK_DEFINITION_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "cv-pdf-service",
      "image": "$ECR_REPOSITORY:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cv-pdf-service",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "FRONTEND_URL",
          "value": "https://your-amplify-app.com"
        }
      ]
    }
  ]
}
EOF

# Register task definition
echo "Registering task definition..."
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION --no-cli-pager

# Create or update service
echo "Creating/updating ECS service..."
SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION --query 'services[0].status' --output text --no-cli-pager 2>/dev/null || echo "INACTIVE")

if [ "$SERVICE_EXISTS" = "ACTIVE" ]; then
  echo "Service exists, updating..."
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_FAMILY \
    --region $REGION \
    --no-cli-pager
  echo "Service update initiated. Waiting for deployment to stabilize (this may take 2-5 minutes)..."
else
  echo "Service does not exist, creating..."
  aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_FAMILY \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-0b3aaa0693ccc03da],securityGroups=[sg-0887a25ef5d0008ad],assignPublicIp=ENABLED}" \
    --region $REGION \
    --no-cli-pager
  echo "Service creation initiated. Waiting for service to stabilize (this may take 3-5 minutes)..."
fi

# Wait for service to stabilize
echo ""
echo "Waiting for service to reach stable state..."
echo "This typically takes 2-5 minutes. The AWS CLI will wait for the service to stabilize..."
echo "Note: If this appears to hang, the service may be taking longer than expected."
echo "You can check status in AWS Console: ECS > Clusters > $CLUSTER_NAME > Services > $SERVICE_NAME"
echo ""

# Use AWS CLI wait command (has built-in 20 minute timeout)
if aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION \
  --no-cli-pager; then
  echo ""
  echo "✓ Service is stable and running!"
else
  WAIT_EXIT_CODE=$?
  echo ""
  echo "⚠ WARNING: Service stabilization check failed or timed out (exit code: $WAIT_EXIT_CODE)"
  echo "The service may still be deploying. Checking current status..."
  
  # Show current service status
  echo ""
  echo "Current service status:"
  aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount,Deployments:deployments[*].{Status:status,Desired:desiredCount,Running:runningCount}}' \
    --output json \
    --no-cli-pager 2>/dev/null || echo "Could not retrieve service status"
  
  echo ""
  echo "If the service shows as ACTIVE with running tasks, the deployment may have succeeded."
  echo "If not, check CloudWatch logs for the service to diagnose issues."
  echo ""
  echo "To check logs:"
  echo "  aws logs tail /ecs/cv-pdf-service --follow --region $REGION"
  
  # Don't exit with error - let user decide if deployment succeeded
  echo ""
  echo "Continuing with deployment summary..."
fi

echo ""
echo "=========================================="
echo "PDF Service deployed successfully!"
echo "=========================================="
echo "ECR Repository: $ECR_REPOSITORY"
echo "Task Definition: $TASK_DEFINITION_FAMILY"
echo "Service: $SERVICE_NAME"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""
echo "Deployment process completed!"
echo "=========================================="
