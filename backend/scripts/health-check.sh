#!/bin/bash

# Health Check Script for ML Platform Backend

echo "🏥 ML Platform Health Check"
echo "=========================="

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -f -s -o /dev/null -w "%{http_code}" "$health_url" | grep -q "$expected_status"; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy"
        return 1
    fi
}

# Function to check Docker container status
check_container() {
    local container_name=$1
    echo -n "Checking container $container_name... "
    
    if docker-compose ps | grep "$container_name" | grep -q "Up"; then
        echo "✅ Running"
        return 0
    else
        echo "❌ Not running"
        return 1
    fi
}

# Check Docker containers
echo "📦 Container Status:"
check_container "backend"
check_container "db"
check_container "redis"
check_container "minio"
check_container "worker"

echo ""

# Check service endpoints
echo "🌐 Service Health:"
check_service "Backend API" "http://localhost:8000/health"
check_service "MinIO" "http://localhost:9000/minio/health/live"

echo ""

# Check database connection
echo "🗄️  Database Connection:"
if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis connection
echo "📦 Cache Connection:"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

echo ""

# Resource usage
echo "💻 Resource Usage:"
echo "Docker containers:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6

echo ""

# Show recent logs if there are any errors
echo "📜 Recent Error Logs:"
docker-compose logs --tail=5 backend 2>/dev/null | grep -i error || echo "No recent errors found"

echo ""
echo "🏁 Health check complete!"