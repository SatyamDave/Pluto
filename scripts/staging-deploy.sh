#!/bin/bash

# Staging Deployment Script for AI Market Terminal
# This script deploys the beta version to staging environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"your-registry"}
IMAGE_TAG="0.9.0-beta"
NAMESPACE="ai-market-terminal"
HELM_RELEASE="ai-market-staging"

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
        log_error "Helm is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t ${DOCKER_REGISTRY}/ai-market-api:${IMAGE_TAG} apps/api/
    docker push ${DOCKER_REGISTRY}/ai-market-api:${IMAGE_TAG}
    
    # Build Web image
    log_info "Building Web image..."
    docker build -t ${DOCKER_REGISTRY}/ai-market-web:${IMAGE_TAG} apps/web/
    docker push ${DOCKER_REGISTRY}/ai-market-web:${IMAGE_TAG}
    
    log_success "Docker images built and pushed successfully"
}

# Deploy secrets and config
deploy_secrets() {
    log_info "Deploying secrets and configuration..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets
    kubectl apply -f infra/k8s/staging-secrets.yaml
    
    log_success "Secrets and configuration deployed"
}

# Deploy with Helm
deploy_with_helm() {
    log_info "Deploying with Helm..."
    
    # Add Helm repository if needed
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    # Deploy the application
    helm upgrade --install ${HELM_RELEASE} ./infra/helm \
        --namespace ${NAMESPACE} \
        --values infra/helm/values.staging.yaml \
        --set global.imageRegistry=${DOCKER_REGISTRY} \
        --set global.imageTag=${IMAGE_TAG} \
        --wait \
        --timeout=10m
    
    log_success "Helm deployment completed"
}

# Wait for deployment readiness
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=${HELM_RELEASE} -n ${NAMESPACE} --timeout=300s
    
    # Wait for services to be ready
    kubectl wait --for=condition=ready pod -l app=api -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=web -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s
    
    log_success "All deployments are ready"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check API health
    log_info "Checking API health..."
    API_POD=$(kubectl get pod -l app=api -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec ${API_POD} -n ${NAMESPACE} -- curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check Web application
    log_info "Checking Web application..."
    WEB_POD=$(kubectl get pod -l app=web -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec ${WEB_POD} -n ${NAMESPACE} -- curl -f http://localhost:80/ > /dev/null 2>&1; then
        log_success "Web application check passed"
    else
        log_error "Web application check failed"
        return 1
    fi
    
    # Check database
    log_info "Checking database..."
    DB_POD=$(kubectl get pod -l app=postgres -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec ${DB_POD} -n ${NAMESPACE} -- pg_isready -U ai_market_user -d ai_market_terminal > /dev/null 2>&1; then
        log_success "Database health check passed"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check Redis
    log_info "Checking Redis..."
    REDIS_POD=$(kubectl get pod -l app=redis -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec ${REDIS_POD} -n ${NAMESPACE} -- redis-cli ping > /dev/null 2>&1; then
        log_success "Redis health check passed"
    else
        log_error "Redis health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    # Deploy Prometheus
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace ${NAMESPACE} \
        --set prometheus.prometheusSpec.retention=200h \
        --set grafana.adminPassword=staging_admin_2024 \
        --wait \
        --timeout=10m
    
    # Apply custom Prometheus configuration
    kubectl apply -f infra/monitoring/prometheus.yml -n ${NAMESPACE}
    
    log_success "Monitoring stack deployed"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Run the smoke test script
    if ./scripts/smoke_staging.sh; then
        log_success "Smoke tests passed"
    else
        log_error "Smoke tests failed"
        return 1
    fi
}

# Display deployment information
show_deployment_info() {
    log_success "Staging deployment completed successfully!"
    
    echo ""
    echo "🎉 AI Market Terminal v${IMAGE_TAG} is now deployed to staging!"
    echo ""
    echo "📊 Deployment Information:"
    echo "  Namespace: ${NAMESPACE}"
    echo "  Helm Release: ${HELM_RELEASE}"
    echo "  Image Tag: ${IMAGE_TAG}"
    echo ""
    echo "🌐 Access URLs:"
    echo "  Web Application: https://staging.aimarketterminal.com"
    echo "  API Documentation: https://api.staging.aimarketterminal.com/docs"
    echo "  Grafana Dashboard: https://staging.aimarketterminal.com/grafana (admin/staging_admin_2024)"
    echo "  Prometheus: https://staging.aimarketterminal.com/prometheus"
    echo ""
    echo "🔧 Useful Commands:"
    echo "  kubectl get pods -n ${NAMESPACE}"
    echo "  kubectl get services -n ${NAMESPACE}"
    echo "  kubectl logs -f deployment/api -n ${NAMESPACE}"
    echo "  helm status ${HELM_RELEASE} -n ${NAMESPACE}"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Run smoke tests: ./scripts/smoke_staging.sh"
    echo "  2. Seed demo data: python scripts/seed_staging.py"
    echo "  3. Invite beta testers"
    echo ""
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Rollback Helm release
    helm rollback ${HELM_RELEASE} -n ${NAMESPACE}
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    local action=${1:-"deploy"}
    
    log_info "Starting AI Market Terminal staging deployment..."
    log_info "Action: ${action}"
    log_info "Docker registry: ${DOCKER_REGISTRY}"
    log_info "Image tag: ${IMAGE_TAG}"
    
    case $action in
        "deploy")
            check_prerequisites
            build_and_push_images
            deploy_secrets
            deploy_with_helm
            wait_for_deployment
            run_health_checks
            deploy_monitoring
            run_smoke_tests
            show_deployment_info
            ;;
        "rollback")
            rollback
            ;;
        "health")
            run_health_checks
            ;;
        "smoke")
            run_smoke_tests
            ;;
        *)
            log_error "Unknown action: ${action}"
            echo "Usage: $0 {deploy|rollback|health|smoke}"
            exit 1
            ;;
    esac
}

# Handle script arguments
case "${1:-}" in
    "deploy"|"rollback"|"health"|"smoke")
        main "$1"
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health|smoke}"
        echo ""
        echo "Commands:"
        echo "  deploy    Deploy the application to staging"
        echo "  rollback  Rollback to previous deployment"
        echo "  health    Run health checks"
        echo "  smoke     Run smoke tests"
        echo ""
        echo "Environment variables:"
        echo "  DOCKER_REGISTRY  Docker registry URL (default: your-registry)"
        exit 1
        ;;
esac
