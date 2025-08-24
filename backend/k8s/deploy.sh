#!/bin/bash

# ML Platform Kubernetes Deployment Script

set -e

echo "🚀 Deploying ML Platform to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f namespace.yaml

# Deploy secrets (you should update these with real values)
echo "🔐 Deploying secrets..."
echo "⚠️  WARNING: Update secrets with real values before production deployment!"

# Deploy database
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f postgres.yaml

# Deploy Redis
echo "📦 Deploying Redis..."
kubectl apply -f redis.yaml

# Deploy MinIO
echo "🪣 Deploying MinIO..."
kubectl apply -f minio.yaml

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n ml-platform
kubectl wait --for=condition=available --timeout=300s deployment/redis -n ml-platform

# Deploy MLflow
echo "📊 Deploying MLflow..."
kubectl apply -f mlflow.yaml

# Deploy backend application
echo "🔧 Deploying backend application..."
kubectl apply -f backend.yaml

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ml-platform-backend -n ml-platform

# Deploy JupyterHub
echo "📓 Deploying JupyterHub..."
kubectl apply -f jupyterhub.yaml

# Deploy ingress (optional)
if [ -f ingress.yaml ]; then
    echo "🌐 Deploying ingress..."
    kubectl apply -f ingress.yaml
fi

# Deploy monitoring (optional)
if [ -f monitoring.yaml ]; then
    echo "📈 Deploying monitoring..."
    kubectl apply -f monitoring.yaml
fi

echo "✅ Deployment complete!"
echo ""
echo "📋 Service Status:"
kubectl get pods -n ml-platform
echo ""
echo "🌐 Services:"
kubectl get services -n ml-platform
echo ""
echo "📊 To check deployment status:"
echo "   kubectl get all -n ml-platform"
echo ""
echo "📜 To view logs:"
echo "   kubectl logs -f deployment/ml-platform-backend -n ml-platform"
echo ""
echo "🔧 To access services locally:"
echo "   kubectl port-forward service/ml-platform-backend 8000:8000 -n ml-platform"
echo "   kubectl port-forward service/jupyterhub 8080:8000 -n ml-platform"
echo "   kubectl port-forward service/mlflow 5000:5000 -n ml-platform"