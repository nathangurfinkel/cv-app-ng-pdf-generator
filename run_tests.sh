#!/bin/bash

# PDF Service Test Runner
# Follows Single Responsibility Principle - handles only test execution

set -e

echo "🧪 Running PDF Service Tests..."

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Run unit tests
echo "🔬 Running unit tests..."
pytest tests/unit/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run integration tests
echo "🔗 Running integration tests..."
pytest tests/integration/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run all tests with coverage
echo "📊 Running all tests with coverage..."
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

echo "✅ All tests completed successfully!"
echo "📈 Coverage report generated in htmlcov/index.html"
