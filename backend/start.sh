#!/bin/bash

# ML Platform Backend Startup Script

echo "🚀 Starting ML Cloud Platform Backend..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Create necessary directories
mkdir -p ./storage/models
mkdir -p ./storage/notebooks

# Start the services
echo "📦 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check database
if docker-compose exec -T db pg_isready -U postgres; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not ready"
fi

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "❌ Backend API is not ready"
fi

# Check MinIO
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO storage is ready"
else
    echo "❌ MinIO storage is not ready"
fi

echo ""
echo "🎉 ML Cloud Platform is starting up!"
echo ""
echo "📋 Service URLs:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • MinIO Console: http://localhost:9001 (admin/admin123)"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""

# Show logs for a few seconds
echo "📜 Recent logs:"
docker-compose logs --tail=10