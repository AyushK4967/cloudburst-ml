# ML Cloud Platform Backend Setup Guide

## 🚀 Complete Setup Instructions

This guide will help you set up the complete ML Cloud Platform backend infrastructure with all required components.

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software
1. **Docker & Docker Compose**
   ```bash
   # Install Docker Desktop (includes Docker Compose)
   # Download from: https://www.docker.com/products/docker-desktop
   
   # Verify installation
   docker --version
   docker-compose --version
   ```

2. **Git** (for cloning repository)
   ```bash
   git --version
   ```

3. **Optional: Python 3.10+** (for local development)
   ```bash
   python --version
   ```

## 🔧 Setup Steps

### 1. Project Setup
```bash
# Navigate to your project directory
cd your-project-directory

# The backend directory should already exist with all files
# If not, create it and copy all backend files
```

### 2. Environment Configuration
```bash
# Navigate to backend directory
cd backend

# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
nano .env  # or use your preferred editor
```

### 3. Required Environment Variables

Update your `.env` file with these configurations:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:password@db:5432/mlplatform

# Redis Configuration  
REDIS_URL=redis://redis:6379

# JWT Secret (Change this to a secure random string)
SECRET_KEY=your-super-secure-secret-key-change-this-in-production

# Stripe Configuration (Get from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# Storage Configuration
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_BUCKET=ml-models

# Optional: Local Storage
LOCAL_STORAGE_PATH=./storage
```

### 4. Start the Backend Infrastructure

#### Option A: Quick Start (Recommended)
```bash
# Make start script executable
chmod +x start.sh

# Run the complete setup
./start.sh
```

#### Option B: Manual Setup
```bash
# Create necessary directories
mkdir -p ./storage/models
mkdir -p ./storage/notebooks

# Start all services
docker-compose up -d

# Wait for services to initialize
sleep 30

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check service health
curl http://localhost:8000/health
```

### 5. Verify Installation

After running the setup, verify all services are running:

```bash
# Check running containers
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check database connection
docker-compose exec db pg_isready -U postgres

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check MinIO storage
curl http://localhost:9000/minio/health/live
```

## 🌐 Service URLs

Once everything is running, you can access:

- **API Endpoint**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **MinIO Console**: http://localhost:9001 (admin/admin123)
- **Database**: localhost:5432 (postgres/password)
- **Redis**: localhost:6379

## 🧪 Testing the API

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "username": "testuser",
       "password": "testpassword123",
       "full_name": "Test User"
     }'
```

### 2. Login and Get Token
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "testpassword123"
     }'
```

### 3. Create a Notebook
```bash
# Replace YOUR_TOKEN with the token from login response
curl -X POST "http://localhost:8000/api/notebooks/" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "My Test Notebook",
       "description": "Test notebook for ML experiments",
       "gpu_type": "tesla-t4",
       "cpu_cores": 4,
       "memory_gb": 16
     }'
```

## 🐛 Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker Desktop or Docker service
   sudo systemctl start docker  # Linux
   # Or start Docker Desktop application
   ```

2. **Port conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :8000  # API port
   lsof -i :5432  # Database port
   lsof -i :6379  # Redis port
   lsof -i :9000  # MinIO port
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

3. **Database connection issues**
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d
   
   # Run migrations
   docker-compose exec backend alembic upgrade head
   ```

4. **MinIO bucket creation**
   ```bash
   # Create bucket if it doesn't exist
   docker-compose exec minio mc mb /data/ml-models
   ```

### Viewing Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f minio
```

## 🔒 Security Configuration

### For Production Deployment:

1. **Change Default Passwords**
   - Update PostgreSQL password
   - Update MinIO credentials
   - Generate secure JWT secret key

2. **Environment Variables**
   ```env
   SECRET_KEY=your-super-secure-random-key-64-characters-long
   DATABASE_URL=postgresql://secure_user:secure_password@db:5432/mlplatform
   ```

3. **SSL/TLS Configuration**
   - Enable HTTPS for API endpoints
   - Configure SSL for database connections
   - Use encrypted storage

4. **Network Security**
   - Configure firewall rules
   - Use VPC/private networks
   - Enable authentication for all services

## 📈 Scaling for Production

### Kubernetes Deployment
```bash
# Example Kubernetes deployment
kubectl apply -f k8s/
```

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml ml-platform
```

## 🎯 What You Need to Set Up

### Required:
- ✅ Docker & Docker Compose installed
- ✅ Git (for repository access)
- ✅ Environment variables configured
- ✅ Stripe account and API keys (for billing)

### Optional but Recommended:
- 🔧 Python 3.10+ (for local development)
- 🔧 PostgreSQL client (for database management)
- 🔧 Redis CLI (for cache management)
- 🔧 kubectl (for Kubernetes deployment)

### External Services to Set Up:
1. **Stripe Account**: https://stripe.com
   - Get API keys from dashboard
   - Configure webhooks if needed

2. **Production Database**: (For production)
   - AWS RDS, Google Cloud SQL, or similar
   - Update DATABASE_URL in .env

3. **Production Storage**: (For production)
   - AWS S3, Google Cloud Storage, or similar
   - Update S3 configuration in .env

4. **Monitoring** (Optional):
   - Set up Prometheus + Grafana
   - Configure log aggregation
   - Set up alerts

## ✅ Success Checklist

After setup, you should have:
- [ ] All Docker containers running
- [ ] API responding at http://localhost:8000
- [ ] Database accessible and migrated
- [ ] Redis cache working
- [ ] MinIO storage accessible
- [ ] API documentation available
- [ ] User registration/login working
- [ ] Notebook creation working
- [ ] Model management working
- [ ] Billing system integrated

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f`
3. Verify environment variables
4. Ensure all required ports are available
5. Check Docker and system resources

The ML Cloud Platform backend is now ready for development and testing!