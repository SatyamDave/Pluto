#!/bin/bash

# AI Market Terminal Production Deployment Script
# This script deploys the entire system to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"your-registry"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
NAMESPACE="ai-market-terminal"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is available
    if ! command -v helm &> /dev/null; then
        log_warning "Helm is not installed, skipping Helm chart deployment"
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t ${DOCKER_REGISTRY}/ai-market-api:${IMAGE_TAG} apps/api/
    docker push ${DOCKER_REGISTRY}/ai-market-api:${IMAGE_TAG}
    
    # Build Web image
    log_info "Building Web image..."
    docker build -t ${DOCKER_REGISTRY}/ai-market-web:${IMAGE_TAG} apps/web/
    docker push ${DOCKER_REGISTRY}/ai-market-web:${IMAGE_TAG}
    
    log_success "Docker images built and pushed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Update image tags in manifests
    sed -i "s|ai-market-terminal/api:latest|${DOCKER_REGISTRY}/ai-market-api:${IMAGE_TAG}|g" infra/k8s/api.yaml
    sed -i "s|ai-market-terminal/web:latest|${DOCKER_REGISTRY}/ai-market-web:${IMAGE_TAG}|g" infra/k8s/web.yaml
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f infra/k8s/namespace.yaml
    kubectl apply -f infra/k8s/postgres.yaml
    kubectl apply -f infra/k8s/redis.yaml
    kubectl apply -f infra/k8s/api.yaml
    kubectl apply -f infra/k8s/web.yaml
    kubectl apply -f infra/k8s/ingress.yaml
    
    log_success "Kubernetes deployment completed"
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for API deployment
    kubectl rollout status deployment/api -n ${NAMESPACE} --timeout=300s
    
    # Wait for Web deployment
    kubectl rollout status deployment/web -n ${NAMESPACE} --timeout=300s
    
    # Wait for database
    kubectl rollout status deployment/postgres -n ${NAMESPACE} --timeout=300s
    
    # Wait for Redis
    kubectl rollout status deployment/redis -n ${NAMESPACE} --timeout=300s
    
    log_success "All deployments are ready"
}

# Run health checks
health_checks() {
    log_info "Running health checks..."
    
    # Get service URLs
    API_URL=$(kubectl get service api-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    WEB_URL=$(kubectl get service web-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$API_URL" ]; then
        log_warning "API service not accessible via LoadBalancer, checking ClusterIP"
        API_URL="localhost:8000"
    fi
    
    if [ -z "$WEB_URL" ]; then
        log_warning "Web service not accessible via LoadBalancer, checking ClusterIP"
        WEB_URL="localhost:80"
    fi
    
    # Check API health
    log_info "Checking API health..."
    if curl -f "http://${API_URL}/health" > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check Web application
    log_info "Checking Web application..."
    if curl -f "http://${WEB_URL}/" > /dev/null 2>&1; then
        log_success "Web application check passed"
    else
        log_error "Web application check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    # Deploy Prometheus
    kubectl apply -f infra/monitoring/prometheus.yml -n ${NAMESPACE}
    
    # Deploy Grafana
    kubectl apply -f infra/monitoring/grafana/ -n ${NAMESPACE}
    
    log_success "Monitoring stack deployed"
}

# Deploy with Docker Compose (alternative)
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Load environment variables
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Docker Compose deployment completed"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Rollback API deployment
    kubectl rollout undo deployment/api -n ${NAMESPACE}
    
    # Rollback Web deployment
    kubectl rollout undo deployment/web -n ${NAMESPACE}
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    local deployment_type=${1:-"kubernetes"}
    
    log_info "Starting AI Market Terminal deployment..."
    log_info "Deployment type: ${deployment_type}"
    log_info "Docker registry: ${DOCKER_REGISTRY}"
    log_info "Image tag: ${IMAGE_TAG}"
    
    # Check prerequisites
    check_prerequisites
    
    # Build images
    build_images
    
    # Deploy based on type
    case $deployment_type in
        "kubernetes")
            deploy_kubernetes
            wait_for_deployment
            health_checks
            deploy_monitoring
            ;;
        "docker-compose")
            deploy_docker_compose
            ;;
        *)
            log_error "Unknown deployment type: ${deployment_type}"
            log_info "Supported types: kubernetes, docker-compose"
            exit 1
            ;;
    esac
    
    log_success "Deployment completed successfully!"
    
    # Display access information
    echo ""
    echo "🎉 AI Market Terminal is now deployed!"
    echo ""
    echo "Access URLs:"
    echo "  Web Application: http://localhost (or your domain)"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Grafana Dashboard: http://localhost:3000 (admin/admin)"
    echo "  Prometheus: http://localhost:9090"
    echo ""
    echo "For Kubernetes deployment:"
    echo "  kubectl get pods -n ${NAMESPACE}"
    echo "  kubectl get services -n ${NAMESPACE}"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    "kubernetes"|"docker-compose")
        main "$1"
        ;;
    "rollback")
        rollback
        ;;
    "health")
        health_checks
        ;;
    *)
        echo "Usage: $0 {kubernetes|docker-compose|rollback|health}"
        echo ""
        echo "Commands:"
        echo "  kubernetes     Deploy to Kubernetes cluster"
        echo "  docker-compose Deploy using Docker Compose"
        echo "  rollback       Rollback to previous deployment"
        echo "  health         Run health checks"
        echo ""
        echo "Environment variables:"
        echo "  DOCKER_REGISTRY  Docker registry URL (default: your-registry)"
        echo "  IMAGE_TAG        Docker image tag (default: latest)"
        exit 1
        ;;
esac
