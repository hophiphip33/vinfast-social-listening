#!/bin/bash

# Development Environment Startup Script
# Starts all services for local development

echo "🔧 Starting VinFast Social Listening Platform (Development Mode)..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp .env.example .env
fi

# Function to check if port is available
check_port() {
    if lsof -i:$1 >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking required ports..."
check_port 3000 || echo "Frontend port 3000 in use"
check_port 8000 || echo "Backend port 8000 in use"
check_port 27017 || echo "MongoDB port 27017 in use"

# Start MongoDB in Docker if not running
if ! docker ps | grep -q "vinfast-mongodb"; then
    echo "🗄️ Starting MongoDB..."
    docker run -d \
        --name vinfast-mongodb \
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=vinfast123 \
        -e MONGO_INITDB_DATABASE=vinfast_social_listening \
        -v mongodb_data:/data/db \
        mongo:7.0
fi

# Start Redis in Docker if not running
if ! docker ps | grep -q "vinfast-redis"; then
    echo "🔄 Starting Redis..."
    docker run -d \
        --name vinfast-redis \
        -p 6379:6379 \
        redis:7-alpine
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Function to start backend
start_backend() {
    echo "🐍 Starting backend API..."
    cd backend
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r ../requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Start the API
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to start frontend
start_frontend() {
    echo "⚛️  Starting frontend dashboard..."
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Start React development server
    npm start
}

# Start services based on argument
case "${1:-all}" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        echo "🎯 Starting all services..."
        
        # Start backend in background
        (start_backend) &
        BACKEND_PID=$!
        
        # Wait a bit for backend to start
        sleep 10
        
        # Start frontend
        start_frontend &
        FRONTEND_PID=$!
        
        # Wait for both processes
        wait $BACKEND_PID $FRONTEND_PID
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        echo "  backend  - Start only backend API"
        echo "  frontend - Start only frontend dashboard"
        echo "  all      - Start all services (default)"
        exit 1
        ;;
esac
