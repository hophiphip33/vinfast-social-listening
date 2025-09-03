#!/bin/bash

# VinFast Social Listening Platform Setup Script
# This script sets up the development environment

echo "🚀 Setting up VinFast Social Listening Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p ml-models
mkdir -p data/raw
mkdir -p data/processed
mkdir -p config/ssl

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Install Python dependencies for local development
if command -v python3 &> /dev/null; then
    echo "🐍 Installing Python dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    echo "✅ Python dependencies installed"
fi

# Install Node.js dependencies for frontend
if command -v npm &> /dev/null; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
fi

# Download Vietnamese NLP models
echo "🤖 Downloading Vietnamese NLP models..."
python3 -c "
import os
os.makedirs('ml-models', exist_ok=True)

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    
    print('Downloading PhoBERT Vietnamese sentiment model...')
    model_name = 'wonrax/phobert-base-vietnamese-sentiment'
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir='./ml-models')
    model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir='./ml-models')
    
    print('✅ Vietnamese sentiment model downloaded successfully')
except Exception as e:
    print(f'⚠️  Warning: Could not download models - {e}')
    print('Models will be downloaded on first use')
"

# Set up Git hooks (if in a git repository)
if [ -d ".git" ]; then
    echo "📋 Setting up Git hooks..."
    if [ -f ".pre-commit-config.yaml" ]; then
        pip install pre-commit
        pre-commit install
        echo "✅ Pre-commit hooks installed"
    fi
fi

# Create basic Kubernetes manifests
echo "☸️  Creating Kubernetes deployment files..."
mkdir -p deployment/k8s

cat > deployment/k8s/namespace.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: vinfast-social-listening
EOF

cat > deployment/k8s/mongodb.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
  namespace: vinfast-social-listening
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: admin
        - name: MONGO_INITDB_ROOT_PASSWORD
          value: vinfast123
        - name: MONGO_INITDB_DATABASE
          value: vinfast_social_listening
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
      volumes:
      - name: mongodb-data
        persistentVolumeClaim:
          claimName: mongodb-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: vinfast-social-listening
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
EOF

echo "✅ Basic Kubernetes files created"

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'docker-compose up' to start the platform"
echo "3. Access the dashboard at http://localhost:3000"
echo "4. Access the API at http://localhost:8000"
echo "5. View API documentation at http://localhost:8000/docs"
echo ""
echo "For development:"
echo "- Backend: 'cd backend && python -m uvicorn api.main:app --reload'"
echo "- Frontend: 'cd frontend && npm start'"
echo ""
