#!/bin/bash

# Complete API Gateway Configuration Script
# This script completes the API Gateway setup using existing resources

set -e

# Configuration
API_ID="5pvdzkly00"
ROOT_RESOURCE_ID="s9tnefgvhb"
AI_RESOURCE_ID="4w6b8w"
PDF_RESOURCE_ID="xt9od1"
AI_PROXY_RESOURCE_ID="3k4lfp"
PDF_PROXY_RESOURCE_ID="22fu1c"
REGION="eu-north-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AI_FUNCTION_ARN="arn:aws:lambda:eu-north-1:$ACCOUNT_ID:function:cv-builder-ai-service"

echo "🚀 Completing API Gateway configuration..."

# Add Lambda permission for API Gateway
echo "🔐 Adding Lambda permission for API Gateway..."
aws lambda add-permission \
    --function-name cv-builder-ai-service \
    --statement-id apigateway-invoke-$(date +%s) \
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
    --region $REGION || echo "OPTIONS method may already exist"

# Create OPTIONS method for CORS on PDF resource
echo "🌐 Creating OPTIONS method for CORS on PDF resource..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION || echo "OPTIONS method may already exist"

# Create ANY method for AI service (Lambda integration)
echo "🔗 Creating ANY method for AI service..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $REGION || echo "ANY method may already exist"

# Create ANY method for PDF service (HTTP integration)
echo "🔗 Creating ANY method for PDF service..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $REGION || echo "ANY method may already exist"

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

# For now, let's create a simple Lambda function to proxy PDF requests
echo "📝 Creating PDF proxy Lambda function..."
cat > pdf-proxy-lambda.py << 'EOF'
import json
import boto3
import requests
import os

def lambda_handler(event, context):
    # Get the PDF service URL from environment variables
    pdf_service_url = os.environ.get('PDF_SERVICE_URL', 'http://localhost:8000')
    
    # Extract the path and method from the event
    path = event.get('pathParameters', {}).get('proxy', '')
    http_method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    body = event.get('body', '')
    
    # Construct the full URL
    full_url = f"{pdf_service_url}/{path}"
    
    # Prepare headers for the request
    request_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'API-Gateway-Proxy'
    }
    
    # Add CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    try:
        # Make the request to the PDF service
        if http_method == 'GET':
            response = requests.get(full_url, headers=request_headers, timeout=30)
        elif http_method == 'POST':
            response = requests.post(full_url, headers=request_headers, data=body, timeout=30)
        elif http_method == 'PUT':
            response = requests.put(full_url, headers=request_headers, data=body, timeout=30)
        elif http_method == 'DELETE':
            response = requests.delete(full_url, headers=request_headers, timeout=30)
        else:
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Return the response
        return {
            'statusCode': response.status_code,
            'headers': {**cors_headers, **dict(response.headers)},
            'body': response.text
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Request failed: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Internal error: {str(e)}'})
        }
EOF

# Create a deployment package for the PDF proxy Lambda
echo "📦 Creating PDF proxy Lambda deployment package..."
mkdir -p pdf-proxy-lambda
cp pdf-proxy-lambda.py pdf-proxy-lambda/lambda_function.py
cd pdf-proxy-lambda
zip -r ../pdf-proxy-lambda.zip .
cd ..
rm -rf pdf-proxy-lambda

# Create the PDF proxy Lambda function
echo "🔧 Creating PDF proxy Lambda function..."
aws lambda create-function \
    --function-name cv-pdf-proxy \
    --runtime python3.11 \
    --role arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://pdf-proxy-lambda.zip \
    --memory-size 256 \
    --timeout 60 \
    --environment Variables='{PDF_SERVICE_URL=http://localhost:8000}' \
    --region $REGION || echo "PDF proxy Lambda may already exist"

# Configure Lambda integration for PDF service
echo "⚙️ Configuring Lambda integration for PDF service..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$REGION:$ACCOUNT_ID:function:cv-pdf-proxy/invocations" \
    --region $REGION

# Add Lambda permission for PDF proxy
echo "🔐 Adding Lambda permission for PDF proxy..."
aws lambda add-permission \
    --function-name cv-pdf-proxy \
    --statement-id apigateway-invoke-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*/*" \
    --region $REGION || echo "Permission may already exist"

# Configure CORS for AI service
echo "🌐 Configuring CORS for AI service..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true,"method.response.header.Access-Control-Allow-Methods": true,"method.response.header.Access-Control-Allow-Origin": true}' \
    --region $REGION || echo "Method response may already exist"

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --integration-http-method OPTIONS \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION || echo "Integration may already exist"

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $AI_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin": "'\''*'\''"}' \
    --region $REGION || echo "Integration response may already exist"

# Configure CORS for PDF service
echo "🌐 Configuring CORS for PDF service..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true,"method.response.header.Access-Control-Allow-Methods": true,"method.response.header.Access-Control-Allow-Origin": true}' \
    --region $REGION || echo "Method response may already exist"

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --integration-http-method OPTIONS \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION || echo "Integration may already exist"

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $PDF_PROXY_RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin": "'\''*'\''"}' \
    --region $REGION || echo "Integration response may already exist"

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
    "integration": "Lambda Proxy (cv-pdf-proxy)",
    "proxyFunctionArn": "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:cv-pdf-proxy"
  }
}
EOF

echo "📄 API Gateway summary saved to api-gateway-summary.json"
echo "🎉 Setup complete!"

# Clean up
rm -f pdf-proxy-lambda.py pdf-proxy-lambda.zip
