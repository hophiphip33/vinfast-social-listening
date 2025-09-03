#!/bin/bash

# VinFast Social Listening Platform Deployment Script
# Deploys the platform to Kubernetes cluster

echo "🚀 Deploying VinFast Social Listening Platform to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm first."
    exit 1
fi

# Set variables
NAMESPACE="vinfast-social-listening"
CHART_PATH="./deployment/helm-chart"
RELEASE_NAME="vinfast-social-listening"

# Create namespace if it doesn't exist
echo "📁 Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Install MongoDB using Helm (if not using cloud database)
echo "🗄️ Setting up MongoDB..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm upgrade --install mongodb bitnami/mongodb \
  --namespace $NAMESPACE \
  --set auth.rootUsername=admin \
  --set auth.rootPassword=vinfast123 \
  --set auth.database=vinfast_social_listening \
  --set persistence.size=20Gi \
  --set resources.limits.memory=2Gi \
  --set resources.requests.memory=1Gi

# Install Redis for task queue
echo "🔄 Setting up Redis..."
helm upgrade --install redis bitnami/redis \
  --namespace $NAMESPACE \
  --set auth.enabled=false \
  --set master.persistence.size=5Gi

# Build and push Docker images (adjust for your registry)
echo "🐳 Building and pushing Docker images..."
REGISTRY="your-registry.com"  # Change this to your container registry

# Tag and push backend image
docker build -f Dockerfile.backend -t $REGISTRY/vinfast-backend:latest .
docker push $REGISTRY/vinfast-backend:latest

# Tag and push frontend image
docker build -f Dockerfile.frontend -t $REGISTRY/vinfast-frontend:latest .
docker push $REGISTRY/vinfast-frontend:latest

# Deploy the main application
echo "📦 Deploying application..."
if [ -d "$CHART_PATH" ]; then
    helm upgrade --install $RELEASE_NAME $CHART_PATH \
      --namespace $NAMESPACE \
      --set backend.image.repository=$REGISTRY/vinfast-backend \
      --set frontend.image.repository=$REGISTRY/vinfast-frontend \
      --set backend.image.tag=latest \
      --set frontend.image.tag=latest \
      --wait --timeout=600s
else
    # Deploy using kubectl if Helm chart doesn't exist
    kubectl apply -f deployment/k8s/ -n $NAMESPACE
fi

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/vinfast-backend -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/vinfast-frontend -n $NAMESPACE

# Get service URLs
echo "🌐 Getting service information..."
kubectl get services -n $NAMESPACE

# Get ingress information if available
if kubectl get ingress -n $NAMESPACE &> /dev/null; then
    echo "📡 Ingress information:"
    kubectl get ingress -n $NAMESPACE
fi

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Access your application:"
echo "- Frontend: kubectl port-forward svc/vinfast-frontend 3000:3000 -n $NAMESPACE"
echo "- Backend API: kubectl port-forward svc/vinfast-backend 8000:8000 -n $NAMESPACE"
echo ""
echo "To check status:"
echo "kubectl get pods -n $NAMESPACE"
echo "kubectl logs -f deployment/vinfast-backend -n $NAMESPACE"
echo ""
