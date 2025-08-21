#!/bin/bash

# Medical Knowledge Graph Docker Deployment Script
# Builds and deploys enhanced AutoFlow containers for critical care medicine

set -e

echo "🏥 Building Enhanced AutoFlow Medical Knowledge Graph Containers"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose found"

# Create required directories
print_info "Creating required directories..."
mkdir -p data redis-data medical-models benchmark-results docker
print_status "Directories created"

# Copy environment configuration
if [ ! -f .env ]; then
    print_info "Creating medical environment configuration..."
    cp .env.medical .env
    print_warning "Please customize .env with your database credentials and API keys"
else
    print_info "Using existing .env file"
fi

# Build enhanced containers
print_info "Building enhanced medical knowledge graph containers..."

echo ""
print_info "🔨 Building enhanced backend container..."
docker build -f backend/Dockerfile.enhanced -t autoflow-backend-medical:latest backend/

print_status "Enhanced backend container built"

echo ""
print_info "🔨 Building enhanced frontend container..."
docker build -f frontend/Dockerfile.enhanced -t autoflow-frontend-medical:latest .

print_status "Enhanced frontend container built"

echo ""
print_info "🔨 Building benchmark container..."
docker build -f docker/Dockerfile.benchmark -t autoflow-benchmark:latest .

print_status "Benchmark container built"

# Deploy containers
print_info "Deploying enhanced medical knowledge graph stack..."

echo ""
print_info "🚀 Starting enhanced AutoFlow medical services..."
docker-compose -f docker-compose.enhanced.yml up -d

print_status "Enhanced medical knowledge graph deployment complete!"

echo ""
print_info "📊 Service Status:"
docker-compose -f docker-compose.enhanced.yml ps

echo ""
print_info "🏥 Medical Knowledge Graph Services:"
echo "  - Frontend (Medical UI): http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - Background Worker: http://localhost:5555"
echo "  - Redis Cache: localhost:6379"

echo ""
print_info "🧪 To run medical knowledge benchmarks:"
echo "  docker-compose -f docker-compose.enhanced.yml --profile benchmark up kg-benchmark"

echo ""
print_info "📋 To view logs:"
echo "  docker-compose -f docker-compose.enhanced.yml logs -f backend-enhanced"
echo "  docker-compose -f docker-compose.enhanced.yml logs -f frontend-enhanced"

echo ""
print_info "🔧 To enable additional services:"
echo "  Local embedding: docker-compose -f docker-compose.enhanced.yml --profile local-embedding-reranker up -d"
echo "  Separate KG DB: docker-compose -f docker-compose.enhanced.yml --profile separate-db up -d"

echo ""
print_warning "⚠️  Remember to:"
echo "  1. Configure your .env file with proper database credentials"
echo "  2. Run database migrations: docker-compose exec backend-enhanced alembic upgrade head"
echo "  3. Upload medical literature to test the enhanced KG features"
echo "  4. Monitor performance using the medical sample queries"

echo ""
print_status "🎉 Medical Knowledge Graph deployment complete!"
print_status "Ready to process critical care pharmacology with enhanced entity deduplication, semantic relationship typing, and parallel processing!"
