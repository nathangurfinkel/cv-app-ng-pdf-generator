#!/bin/bash

# API Gateway Setup Script for CV Builder Microservices
# This script configures API Gateway to route requests to both AI and PDF services

set -e

# Configuration
API_ID="5pvdzkly00"
ROOT_RESOURCE_ID="s9tnefgvhb"
REGION="eu-north-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AI_FUNCTION_ARN="arn:aws:lambda:eu-north-1:$ACCOUNT_ID:function:cv-builder-ai-service"
PDF_SERVICE_URL="https://placeholder-pdf-service-url.com"  # We'll update this after Fargate is running

echo "🚀 Setting up API Gateway for CV Builder Microservices..."

# Create /ai resource
echo "📝 Creating /ai resource..."
AI_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part ai \
    --region $REGION \
    --query 'id' --output text)

# Create /pdf resource
echo "📝 Creating /pdf resource..."
PDF_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part pdf \
    --region $REGION \
    --query 'id' --output text)

# Create /ai/{proxy+} resource for all AI endpoints
echo "📝 Creating /ai/{proxy+} resource..."
AI_PROXY_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $AI_RESOURCE_ID \
    --path-part '{proxy+}' \
    --region $REGION \
    --query 'id' --output text)

# Create /pdf/{proxy+} resource for all PDF endpoints
echo "📝 Creating /pdf/{proxy+} resource..."
PDF_PROXY_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PDF_RESOURCE_ID \
    --path-part '{proxy+}' \
    --region $REGION \
    --query 'id' --output text)

# Add Lambda permission for API Gateway
echo "🔐 Adding Lambda permission for API Gateway..."
aws lambda add-permission \
    --function-name cv-builder-ai-service \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
    --region $REGION || echo "Permission may already exist"

# Create OPTIONS method for CORS on AI resource
echo "🌐 Creating OPTIONS method for CORS on AI resource..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

# Create OPTIONS method for CORS on PDF resource
echo "🌐 Creating OPTIONS method for CORS on PDF resource..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION

# Create ANY method for AI service (Lambda integration)
echo "🔗 Creating ANY method for AI service..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $REGION

# Create ANY method for PDF service (HTTP integration)
echo "🔗 Creating ANY method for PDF service..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $REGION

# Configure Lambda integration for AI service
echo "⚙️ Configuring Lambda integration for AI service..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$AI_FUNCTION_ARN/invocations" \
    --region $REGION

# Configure HTTP integration for PDF service
echo "⚙️ Configuring HTTP integration for PDF service..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method ANY \
    --type HTTP_PROXY \
    --integration-http-method ANY \
    --uri "$PDF_SERVICE_URL/{proxy}" \
    --region $REGION

# Configure CORS for AI service
echo "🌐 Configuring CORS for AI service..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true,"method.response.header.Access-Control-Allow-Methods": true,"method.response.header.Access-Control-Allow-Origin": true}' \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --integration-http-method OPTIONS \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin": "'\''*'\''"}' \
    --region $REGION

# Configure CORS for PDF service
echo "🌐 Configuring CORS for PDF service..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true,"method.response.header.Access-Control-Allow-Methods": true,"method.response.header.Access-Control-Allow-Origin": true}' \
    --region $REGION

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --integration-http-method OPTIONS \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin": "'\''*'\''"}' \
    --region $REGION

# Deploy the API
echo "🚀 Deploying API Gateway..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION

# Get the API Gateway URL
API_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
echo "✅ API Gateway configured successfully!"
echo "🔗 API Gateway URL: $API_URL"
echo "📋 AI Service endpoints: $API_URL/ai/*"
echo "📋 PDF Service endpoints: $API_URL/pdf/*"

# Create a summary file
cat > api-gateway-summary.json << EOF
{
  "apiId": "$API_ID",
  "apiUrl": "$API_URL",
  "region": "$REGION",
  "aiService": {
    "endpoints": [
      "$API_URL/ai/extract-cv-data",
      "$API_URL/ai/tailor-cv",
      "$API_URL/ai/evaluate-cv",
      "$API_URL/ai/rephrase-section",
      "$API_URL/ai/get-template-recommendation"
    ],
    "integration": "AWS Lambda",
    "functionArn": "$AI_FUNCTION_ARN"
  },
  "pdfService": {
    "endpoints": [
      "$API_URL/pdf/generate",
      "$API_URL/pdf/templates",
      "$API_URL/pdf/health"
    ],
    "integration": "HTTP Proxy",
    "serviceUrl": "$PDF_SERVICE_URL"
  }
}
EOF

echo "📄 API Gateway summary saved to api-gateway-summary.json"
echo "🎉 Setup complete!"
