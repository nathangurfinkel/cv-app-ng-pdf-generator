# PDF Service Integration Tests

These tests verify PDF generation and SSRF protection.

## Prerequisites

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

2. Set environment variables:
```bash
export PDF_SERVICE_URL="http://localhost:8001"  # or your deployed service URL
```

## Running Tests

### Run all integration tests:
```bash
pytest tests/integration/ -v
```

### Run specific test file:
```bash
pytest tests/integration/test_pdf_generation.py -v
pytest tests/integration/test_og_images.py -v
```

## Test Coverage

- **test_pdf_generation.py**: Tests PDF generation with SSRF protection
- **test_og_images.py**: Tests OG image generation for social sharing

## Notes

- These tests require the PDF service to be running (locally or deployed)
- SSRF protection tests verify that invalid origins are rejected
- Tests use real HTTP requests to verify deployed contracts

