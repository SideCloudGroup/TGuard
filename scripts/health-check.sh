#!/bin/bash

# TGuard Health Check Script
# Checks if all services are running properly

set -e

echo "🔍 TGuard Health Check"
echo "====================="

BASE_URL=${BASE_URL:-"http://localhost:8000"}

# Check if Docker containers are running
echo "🐳 Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Some Docker containers are not running!"
    echo "Run: docker-compose up -d"
    exit 1
fi
echo "✅ Docker containers are running"

# Check PostgreSQL
echo "🗄️  Checking PostgreSQL..."
if ! docker-compose exec postgres pg_isready -U postgres &> /dev/null; then
    echo "❌ PostgreSQL is not ready!"
    exit 1
fi
echo "✅ PostgreSQL is healthy"

# Check API health endpoint
echo "🌐 Checking API health..."
if ! curl -s "${BASE_URL}/health" | grep -q "healthy"; then
    echo "❌ API health check failed!"
    echo "Check API logs: docker-compose logs api"
    exit 1
fi
echo "✅ API is healthy"

# Check detailed health
echo "🔍 Checking detailed health..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health/detailed")
if echo "$HEALTH_RESPONSE" | grep -q '"status": "unhealthy"'; then
    echo "❌ Detailed health check failed!"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi
echo "✅ Detailed health check passed"

# Check captcha config
echo "🔐 Checking captcha configuration..."
if ! curl -s "${BASE_URL}/api/v1/captcha-config" | grep -q "siteKey"; then
    echo "❌ Captcha configuration check failed!"
    exit 1
fi
echo "✅ Captcha configuration is valid"

# Summary
echo ""
echo "🎉 All health checks passed!"
echo "✅ TGuard is running properly"
echo ""
echo "🔗 Endpoints:"
echo "  • API: ${BASE_URL}"
echo "  • Health: ${BASE_URL}/health"
echo "  • Verification: ${BASE_URL}/verify"
echo ""
echo "📊 Monitoring:"
echo "  • Logs: docker-compose logs -f"
echo "  • Status: docker-compose ps"
