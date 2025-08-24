# ML Platform Production Setup Guide

## Overview
This guide covers deploying the ML Platform to production using Kubernetes for scalability and reliability.

## Prerequisites

### Required Tools
- **Kubernetes Cluster**: EKS, GKE, AKS, or self-managed
- **kubectl**: Kubernetes command-line tool
- **Helm**: Package manager for Kubernetes (optional but recommended)
- **Docker**: For building custom images
- **Domain**: For external access (e.g., mlplatform.com)

### Infrastructure Requirements
- **GPU Nodes**: NVIDIA GPU nodes for ML workloads
- **Storage**: Persistent storage for databases and model artifacts
- **Load Balancer**: For distributing traffic
- **SSL/TLS**: Certificate management

## Deployment Steps

### 1. Cluster Preparation

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Install NVIDIA GPU operator (for GPU support)
helm repo add nvidia https://nvidia.github.io/gpu-operator
helm install --wait gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --create-namespace

# Install ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-system \
  --create-namespace
```

### 2. Secrets Management

```bash
# Create secrets for sensitive data
kubectl create secret generic postgres-secret \
  --from-literal=password=your-secure-postgres-password \
  -n ml-platform

kubectl create secret generic backend-secret \
  --from-literal=secret-key=your-jwt-secret-key \
  --from-literal=stripe-secret-key=your-stripe-secret-key \
  -n ml-platform
```

### 3. Deploy Infrastructure

```bash
# Deploy in order
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/minio.yaml

# Wait for databases to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n ml-platform
```

### 4. Deploy Applications

```bash
# Deploy MLflow
kubectl apply -f k8s/mlflow.yaml

# Deploy backend
kubectl apply -f k8s/backend.yaml

# Deploy JupyterHub
kubectl apply -f k8s/jupyterhub.yaml

# Deploy monitoring
kubectl apply -f k8s/monitoring.yaml
```

### 5. Configure Ingress

```bash
# Deploy ingress with SSL
kubectl apply -f k8s/ingress.yaml
```

## Production Configuration

### Environment Variables
Update these in `k8s/backend.yaml`:

```yaml
env:
- name: DATABASE_URL
  value: "postgresql://postgres:$(POSTGRES_PASSWORD)@postgres:5432/mlplatform"
- name: STRIPE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: backend-secret
      key: stripe-secret-key
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: backend-secret
      key: secret-key
```

### Resource Allocation

#### Backend Application
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1"
```

#### Database
```yaml
resources:
  requests:
    memory: "2Gi" 
    cpu: "1"
  limits:
    memory: "4Gi"
    cpu: "2"
```

### Auto-scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: ml-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-platform-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## SSL/TLS Configuration

### Using cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Monitoring Setup

### Prometheus Configuration
Located in `k8s/monitoring.yaml`:
- Scrapes metrics from all services
- Stores metrics for 7 days
- Configured for Kubernetes service discovery

### Grafana Dashboards
- Pre-configured dashboard in `monitoring/grafana-dashboard.json`
- Default admin password: `admin123` (change in production)
- Access: `https://grafana.yourdomain.com`

### Alerting Rules
Create alerting rules for:
- High CPU/Memory usage
- Database connection issues
- Failed notebook startups
- Model deployment failures

## Backup Strategy

### Database Backup
```bash
# Create backup cronjob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: ml-platform
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgres -U postgres mlplatform > /backup/backup-$(date +%Y%m%d_%H%M%S).sql
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
EOF
```

### MinIO Backup
- Configure cross-region replication
- Set up lifecycle policies for old artifacts
- Regular backup to external storage

## Security Checklist

### Network Security
- [ ] Network policies implemented
- [ ] Private subnets for databases
- [ ] VPC/firewall rules configured
- [ ] Load balancer security groups

### Application Security
- [ ] Secrets stored in Kubernetes secrets
- [ ] RBAC configured for JupyterHub
- [ ] API rate limiting enabled
- [ ] Input validation on all endpoints

### Container Security
- [ ] Container images scanned for vulnerabilities
- [ ] Non-root user in containers
- [ ] Resource limits set on all containers
- [ ] Security contexts configured

## Performance Optimization

### Database Optimization
```sql
-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

### Redis Optimization
```yaml
# Redis configuration
config: |
  maxmemory 512mb
  maxmemory-policy volatile-lru
  save 900 1
  save 300 10
  save 60 10000
```

### Application Optimization
- Enable connection pooling
- Implement caching for frequent queries  
- Use async operations where possible
- Optimize database queries with indexes

## Scaling Guidelines

### Horizontal Scaling
- Backend: 3-10 replicas based on load
- Workers: 2-20 replicas based on job queue
- Database: Consider read replicas for high read loads

### Vertical Scaling
- Increase memory for ML workloads
- GPU nodes for training tasks
- Fast storage for model artifacts

### Auto-scaling Metrics
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Queue depth for background tasks
- Response time SLA

## Troubleshooting

### Common Issues

#### Pod Startup Failures
```bash
# Check pod logs
kubectl logs -f deployment/ml-platform-backend -n ml-platform

# Check events
kubectl get events -n ml-platform --sort-by='.lastTimestamp'
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/postgres -n ml-platform -- psql -U postgres -d mlplatform -c "SELECT 1;"
```

#### Storage Issues
```bash
# Check persistent volumes
kubectl get pv,pvc -n ml-platform

# Check storage usage
kubectl exec -it deployment/postgres -n ml-platform -- df -h
```

### Health Checks
All services include health checks:
- Liveness probes: Restart unhealthy containers
- Readiness probes: Remove from load balancer when not ready
- Startup probes: Allow slow-starting containers

## Maintenance

### Regular Tasks
- Update container images monthly
- Review and rotate secrets quarterly
- Clean up old model artifacts
- Monitor resource usage trends
- Update Kubernetes cluster

### Upgrade Process
1. Test in staging environment
2. Create database backup
3. Rolling update deployments
4. Verify functionality
5. Monitor for issues

## Cost Optimization

### Resource Management
- Use resource quotas per namespace
- Implement pod disruption budgets
- Use spot instances for non-critical workloads
- Schedule GPU workloads efficiently

### Storage Optimization
- Implement object lifecycle policies
- Compress model artifacts
- Use appropriate storage classes
- Clean up unused resources

## Support and Monitoring

### Logging
- Centralized logging with ELK/EFK stack
- Log aggregation from all services
- Log retention policies

### Metrics
- Custom metrics for business logic
- Infrastructure metrics
- Application performance metrics

### Alerting
- PagerDuty/Slack integration
- Escalation policies
- Runbook documentation

## Disaster Recovery

### Recovery Time Objectives (RTO)
- Critical services: < 15 minutes
- Non-critical services: < 1 hour
- Data recovery: < 4 hours

### Recovery Process
1. Restore from backup
2. Recreate infrastructure
3. Deploy applications
4. Verify functionality
5. Resume operations

This production setup provides a robust, scalable, and secure ML platform ready for enterprise use.