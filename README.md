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

## Environment Variables

Create a `.env` file with the following variables:

```env
# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.com

# Debug Configuration
DEBUG=false
VERBOSE=false

# Frontend URL (for PDF generation)
FRONTEND_URL=https://your-amplify-app.com
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your actual values
```

3. Run locally:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## Deployment to AWS Fargate

1. Build and push to ECR:
```bash
# Build the image
docker build -t cv-pdf-service .

# Tag for ECR
docker tag cv-pdf-service:latest {account-id}.dkr.ecr.{region}.amazonaws.com/cv-pdf-service:latest

# Push to ECR
docker push {account-id}.dkr.ecr.{region}.amazonaws.com/cv-pdf-service:latest
```

2. Create Fargate service using AWS CLI or console
3. Configure API Gateway to route `/pdf/*` requests to this Fargate service

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
