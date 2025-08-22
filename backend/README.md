# ML Cloud Platform Backend

A complete backend infrastructure for a cloud-based ML platform with Jupyter notebooks, GPU support, model deployment, and pay-as-you-go billing.

## Features

- **User Authentication**: JWT-based authentication system
- **Jupyter Notebooks**: GPU-enabled notebook instances with Docker containers
- **Model Management**: Upload, store, and version ML models
- **Model Deployment**: Deploy models as API endpoints with auto-scaling
- **Billing System**: Pay-as-you-go usage tracking with Stripe integration
- **Storage**: S3-compatible storage (MinIO) for models and data
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis + Celery for background tasks
- **Containers**: Docker for notebook and deployment isolation
- **Storage**: MinIO (S3-compatible) for object storage
- **Payments**: Stripe for billing
- **Authentication**: JWT tokens with bcrypt password hashing

## Quick Start

1. **Prerequisites**
   ```bash
   # Install Docker and Docker Compose
   docker --version
   docker-compose --version
   ```

2. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd backend
   ```

3. **Environment Variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/mlplatform
   REDIS_URL=redis://localhost:6379
   SECRET_KEY=your-secret-key-change-in-production
   STRIPE_SECRET_KEY=sk_test_your_stripe_key
   S3_ENDPOINT_URL=http://localhost:9000
   S3_ACCESS_KEY=minioadmin
   S3_SECRET_KEY=minioadmin123
   S3_BUCKET=ml-models
   ```

4. **Start Services**
   ```bash
   docker-compose up -d
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Notebooks
- `GET /api/notebooks/` - List user notebooks
- `POST /api/notebooks/` - Create new notebook
- `POST /api/notebooks/{id}/start` - Start notebook
- `POST /api/notebooks/{id}/stop` - Stop notebook
- `DELETE /api/notebooks/{id}` - Delete notebook

### Models
- `GET /api/models/` - List user models
- `POST /api/models/` - Create new model
- `POST /api/models/{id}/upload` - Upload model file
- `DELETE /api/models/{id}` - Delete model

### Deployments
- `GET /api/deployments/` - List deployments
- `POST /api/deployments/` - Deploy model
- `POST /api/deployments/{id}/predict` - Make prediction
- `DELETE /api/deployments/{id}` - Delete deployment

### Billing
- `GET /api/billing/usage` - Get usage statistics
- `GET /api/billing/stats` - Get detailed billing stats
- `GET /api/billing/pricing` - Get pricing information

## GPU Support

The platform supports multiple GPU types:
- **Tesla T4**: $1.20/hour - Good for inference and light training
- **Tesla V100**: $3.00/hour - High-performance training and inference
- **RTX 4090**: $1.80/hour - Excellent price/performance for most workloads
- **CPU Only**: $0.30/hour - For CPU-based workloads

## Model Deployment

Supported model formats:
- **Scikit-learn**: `.pkl`, `.joblib` files
- **PyTorch**: `.pt`, `.pth` files
- **TensorFlow/Keras**: `.h5`, `.pb` files
- **ONNX**: `.onnx` files

## Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**
   ```bash
   alembic upgrade head
   ```

3. **Start Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Production Deployment

1. **Update Environment Variables**
   - Set strong `SECRET_KEY`
   - Configure production database
   - Add real Stripe keys
   - Configure S3 storage

2. **Use Production Docker Image**
   ```bash
   docker build -t ml-platform-backend .
   docker run -p 8000:8000 ml-platform-backend
   ```

3. **Set up Kubernetes (Recommended)**
   - Deploy with Kubernetes for production scaling
   - Use NVIDIA GPU Operator for GPU support
   - Configure ingress for external access

## Monitoring

- Health check endpoint: `GET /health`
- API metrics tracked automatically
- Usage and billing metrics in database
- Container logs available via Docker

## Security

- JWT tokens for authentication
- API key authentication for model endpoints
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- File upload validation and limits

## Pricing Model

- **Pay-as-you-go**: Charged by the minute for running resources
- **No setup fees**: Only pay for what you use
- **Transparent pricing**: See costs in real-time
- **Multiple payment methods**: Credit card via Stripe

## Support

For issues and feature requests, please create an issue in the repository.