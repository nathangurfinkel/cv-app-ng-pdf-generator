#!/bin/bash

# PDF Service Deployment Script for AWS Fargate
# This script builds and deploys the PDF service to AWS Fargate via ECR

set -e

echo "🚀 Starting PDF Service deployment to AWS Fargate..."

# Configuration
SERVICE_NAME="cv-pdf-service"
CLUSTER_NAME="cv-builder-cluster"
REGION="eu-north-1"  # Stockholm region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/cv-pdf-service"
TASK_DEFINITION_FAMILY="cv-pdf-service"

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t $SERVICE_NAME .

# Tag image for ECR
echo "🏷️ Tagging image for ECR..."
docker tag $SERVICE_NAME:latest $ECR_REPOSITORY:latest

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository if needed..."
aws ecr describe-repositories --repository-names cv-pdf-service --region $REGION &> /dev/null || \
aws ecr create-repository --repository-name cv-pdf-service --region $REGION

# Push image to ECR
echo "⬆️ Pushing image to ECR..."
docker push $ECR_REPOSITORY:latest

# Create task definition
echo "📋 Creating task definition..."
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
echo "📝 Registering task definition..."
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION

# Create or update service
echo "🔄 Creating/updating ECS service..."
aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION &> /dev/null && \
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_DEFINITION_FAMILY --region $REGION || \
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_DEFINITION_FAMILY \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0b3aaa0693ccc03da],securityGroups=[sg-0887a25ef5d0008ad],assignPublicIp=ENABLED}" \
  --region $REGION

echo "✅ PDF Service deployed successfully!"
echo "🔗 ECR Repository: $ECR_REPOSITORY"
echo "📋 Task Definition: $TASK_DEFINITION_FAMILY"
echo "🎉 Deployment process completed!"
