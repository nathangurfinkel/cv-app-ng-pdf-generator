#!/bin/bash

# Setup Application Load Balancer for PDF Service
# This ensures a stable endpoint even when Fargate tasks restart

set -e

echo "Setting up Application Load Balancer for PDF Service..."

REGION="eu-north-1"
CLUSTER_NAME="cv-builder-cluster"
SERVICE_NAME="cv-pdf-service"
VPC_ID="vpc-061fd17132a2adcd6"
SUBNET_1="subnet-0b3aaa0693ccc03da"  # eu-north-1a
SUBNET_2="subnet-0db149ba7ff207df7"  # eu-north-1b
SUBNET_3="subnet-0fed3a782a43d38e5"  # eu-north-1c
SECURITY_GROUP="sg-0887a25ef5d0008ad"

echo "VPC: $VPC_ID"
echo "Subnets: $SUBNET_1, $SUBNET_2, $SUBNET_3"

# Create security group for ALB if it doesn't exist
echo "Creating/checking ALB security group..."
ALB_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=cv-pdf-alb-sg" "Name=vpc-id,Values=$VPC_ID" \
  --region $REGION \
  --query 'SecurityGroups[0].GroupId' \
  --output text 2>/dev/null) || echo "None"

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
  
  echo "Created ALB security group: $ALB_SG_ID"
else
  echo "Using existing ALB security group: $ALB_SG_ID"
fi

# Update ECS task security group to allow traffic from ALB
echo "Updating ECS security group to allow ALB traffic..."
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 8000 \
  --source-group $ALB_SG_ID \
  --region $REGION 2>/dev/null || echo "Rule may already exist"

# Create target group
echo "Creating target group..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --names cv-pdf-tg \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null) || echo "None"

if [ "$TARGET_GROUP_ARN" = "None" ] || [ -z "$TARGET_GROUP_ARN" ]; then
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
    --output text)
  echo "Created Target Group: $TARGET_GROUP_ARN"
else
  echo "Using existing Target Group: $TARGET_GROUP_ARN"
fi

# Create Application Load Balancer
echo "Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names cv-pdf-alb \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null) || echo "None"

if [ "$ALB_ARN" = "None" ] || [ -z "$ALB_ARN" ]; then
  ALB_ARN=$(aws elbv2 create-load-balancer \
    --name cv-pdf-alb \
    --subnets $SUBNET_1 $SUBNET_2 $SUBNET_3 \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)
  echo "Created ALB: $ALB_ARN"
  echo "Waiting for ALB to be active..."
  sleep 10
else
  echo "Using existing ALB: $ALB_ARN"
fi

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --region $REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "ALB DNS: $ALB_DNS"

# Create listener
echo "Creating listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --region $REGION \
  --query 'Listeners[0].ListenerArn' \
  --output text 2>/dev/null) || echo "None"

if [ "$LISTENER_ARN" = "None" ] || [ -z "$LISTENER_ARN" ]; then
  LISTENER_ARN=$(aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --region $REGION \
    --query 'Listeners[0].ListenerArn' \
    --output text)
  echo "Created Listener: $LISTENER_ARN"
else
  echo "Using existing Listener: $LISTENER_ARN"
fi

# Delete the old service and recreate with load balancer
echo "Updating ECS service to use load balancer..."
echo "WARNING: This will recreate the service with load balancer configuration..."

# Update service to 0 desired count first
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 0 \
  --region $REGION

echo "Waiting for tasks to stop..."
sleep 10

# Delete the service
aws ecs delete-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force \
  --region $REGION

echo "Waiting for service deletion..."
sleep 15

# Recreate service with load balancer
echo "Creating new service with load balancer..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition cv-pdf-service \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2,$SUBNET_3],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=cv-pdf-service,containerPort=8000" \
  --health-check-grace-period-seconds 60 \
  --region $REGION

echo ""
echo "=========================================="
echo "LOAD BALANCER SETUP COMPLETE!"
echo "=========================================="
echo "Summary:"
echo "   • ALB DNS: http://$ALB_DNS"
echo "   • Target Group: $TARGET_GROUP_ARN"
echo "   • Health Check: /health"
echo ""
echo "Next Steps:"
echo "   1. Wait 2-3 minutes for service to be healthy"
echo "   2. Test: curl http://$ALB_DNS/health"
echo "   3. Update frontend: VITE_PDF_SERVICE_URL=http://$ALB_DNS"
echo "=========================================="
echo ""
echo "Export for easy access:"
echo "export PDF_ALB_URL=http://$ALB_DNS"



