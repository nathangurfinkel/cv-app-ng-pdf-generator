#!/bin/bash

# Setup Application Load Balancer for PDF Service
# This ensures a stable endpoint even when Fargate tasks restart

set -e

echo "🔧 Setting up Application Load Balancer for PDF Service..."

REGION="eu-north-1"
CLUSTER_NAME="cv-builder-cluster"
SERVICE_NAME="cv-pdf-service"
VPC_ID="vpc-0c1e8b3c7e8e8e8e8"  # We'll detect this
SUBNET_1="subnet-0b3aaa0693ccc03da"
SECURITY_GROUP="sg-0887a25ef5d0008ad"

# Get VPC ID from the subnet
echo "🔍 Detecting VPC..."
VPC_ID=$(aws ec2 describe-subnets --subnet-ids $SUBNET_1 --region $REGION --query 'Subnets[0].VpcId' --output text)
echo "✅ VPC: $VPC_ID"

# Get all subnets in the VPC for the ALB (needs at least 2 AZs)
echo "🔍 Getting subnets in VPC..."
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --query 'Subnets[*].SubnetId' --output text)
echo "✅ Subnets: $SUBNETS"

# Create security group for ALB if it doesn't exist
echo "🔒 Creating/checking ALB security group..."
ALB_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=cv-pdf-alb-sg" "Name=vpc-id,Values=$VPC_ID" \
  --region $REGION \
  --query 'SecurityGroups[0].GroupId' \
  --output text 2>/dev/null) || true

if [ "$ALB_SG_ID" = "None" ] || [ -z "$ALB_SG_ID" ]; then
  echo "Creating new ALB security group..."
  ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name cv-pdf-alb-sg \
    --description "Security group for CV PDF ALB" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' \
    --output text)
  
  # Allow HTTP traffic
  aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION
  
  echo "✅ Created ALB security group: $ALB_SG_ID"
else
  echo "✅ Using existing ALB security group: $ALB_SG_ID"
fi

# Create target group
echo "📊 Creating target group..."
TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
  --name cv-pdf-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-enabled \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 2 \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null) || \
  aws elbv2 describe-target-groups \
    --names cv-pdf-tg \
    --region $REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text

echo "✅ Target Group ARN: $TARGET_GROUP_ARN"

# Create Application Load Balancer
echo "⚖️ Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name cv-pdf-alb \
  --subnets $SUBNETS \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null) || \
  aws elbv2 describe-load-balancers \
    --names cv-pdf-alb \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text

echo "✅ ALB ARN: $ALB_ARN"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --region $REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "✅ ALB DNS: $ALB_DNS"

# Create listener
echo "👂 Creating listener..."
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
  --region $REGION \
  --query 'Listeners[0].ListenerArn' \
  --output text 2>/dev/null) || \
  aws elbv2 describe-listeners \
    --load-balancer-arn $ALB_ARN \
    --region $REGION \
    --query 'Listeners[0].ListenerArn' \
    --output text

echo "✅ Listener ARN: $LISTENER_ARN"

# Update ECS service to use load balancer
echo "🔄 Updating ECS service to use load balancer..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --load-balancers targetGroupArn=$TARGET_GROUP_ARN,containerName=cv-pdf-service,containerPort=8000 \
  --region $REGION \
  --force-new-deployment || echo "Note: Service may need to be recreated with load balancer configuration"

echo ""
echo "="*80
echo "✅ LOAD BALANCER SETUP COMPLETE!"
echo "="*80
echo "📋 Summary:"
echo "   • ALB DNS: http://$ALB_DNS"
echo "   • Target Group: $TARGET_GROUP_ARN"
echo "   • Health Check: /health"
echo ""
echo "🔄 Next Steps:"
echo "   1. Wait 2-3 minutes for ALB to be provisioned"
echo "   2. Test: curl http://$ALB_DNS/health"
echo "   3. Update frontend environment variable to: http://$ALB_DNS"
echo "="*80
