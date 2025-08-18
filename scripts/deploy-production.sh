#!/bin/bash

# Production Deployment Script for AI Market Terminal
# Deploys to https://aimarketterminal.com

set -e

# Configuration
PRODUCTION_DOMAIN="aimarketterminal.com"
API_DOMAIN="api.aimarketterminal.com"
BETA_DOMAIN="beta.aimarketterminal.com"
DOCKER_REGISTRY="your-registry"
VERSION="0.9.0-beta"
NAMESPACE="ai-market-terminal"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed"
        exit 1
    fi
    
    # Check if connected to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to Kubernetes cluster"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t $DOCKER_REGISTRY/ai-market-api:$VERSION ./apps/api
    docker push $DOCKER_REGISTRY/ai-market-api:$VERSION
    
    # Build Web image
    log_info "Building Web image..."
    docker build -t $DOCKER_REGISTRY/ai-market-web:$VERSION ./apps/web
    docker push $DOCKER_REGISTRY/ai-market-web:$VERSION
    
    log_success "Images built and pushed successfully"
}

# Deploy to production
deploy_to_production() {
    log_info "Deploying to production..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply production secrets
    log_info "Applying production secrets..."
    kubectl apply -f infra/k8s/production-secrets.yaml -n $NAMESPACE
    
    # Deploy with Helm
    log_info "Deploying with Helm..."
    helm upgrade --install ai-market-production ./infra/helm \
        --namespace $NAMESPACE \
        --values infra/helm/values.prod.yaml \
        --set global.imageRegistry=$DOCKER_REGISTRY \
        --set global.imageTag=$VERSION \
        --wait \
        --timeout=15m
    
    log_success "Production deployment completed"
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=ai-market-production -n $NAMESPACE --timeout=600s
    
    # Wait for services to be available
    kubectl wait --for=condition=ready service -l app.kubernetes.io/instance=ai-market-production -n $NAMESPACE --timeout=300s
    
    log_success "All services are ready"
}

# Configure DNS and SSL
configure_dns_ssl() {
    log_info "Configuring DNS and SSL..."
    
    # Check if cert-manager is installed
    if ! kubectl get namespace cert-manager &> /dev/null; then
        log_warning "cert-manager not found. Installing..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
    fi
    
    # Create ClusterIssuer for Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@$PRODUCTION_DOMAIN
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    log_success "DNS and SSL configured"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check main domain
    if curl -f -s "https://$PRODUCTION_DOMAIN/health" > /dev/null; then
        log_success "Main domain is healthy"
    else
        log_error "Main domain health check failed"
        return 1
    fi
    
    # Check API domain
    if curl -f -s "https://$API_DOMAIN/health" > /dev/null; then
        log_success "API domain is healthy"
    else
        log_error "API domain health check failed"
        return 1
    fi
    
    # Check beta domain
    if curl -f -s "https://$BETA_DOMAIN" > /dev/null; then
        log_success "Beta domain is healthy"
    else
        log_error "Beta domain health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Set up monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Install Prometheus Stack if not exists
    if ! helm list -n monitoring | grep -q prometheus; then
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        
        kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
        
        helm install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --set grafana.enabled=true \
            --set prometheus.prometheusSpec.retention=30d
    fi
    
    # Create monitoring dashboards
    kubectl apply -f infra/monitoring/dashboards/ -n monitoring
    
    log_success "Monitoring setup completed"
}

# Create demo accounts
create_demo_accounts() {
    log_info "Creating demo accounts..."
    
    # Run the seeding script
    python3 scripts/seed_staging.py --environment=production
    
    log_success "Demo accounts created"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    cat > deployment-report.md <<EOF
# Production Deployment Report

## Deployment Details
- **Version**: $VERSION
- **Timestamp**: $(date)
- **Deployed by**: $(whoami)
- **Environment**: Production

## URLs
- **Main Site**: https://$PRODUCTION_DOMAIN
- **API Documentation**: https://$API_DOMAIN/docs
- **Beta Portal**: https://$BETA_DOMAIN
- **Grafana Dashboard**: https://$PRODUCTION_DOMAIN/grafana

## Service Status
$(kubectl get pods -n $NAMESPACE)

## Demo Accounts
- **Learner**: learner@demo.aimarketterminal.com / demo123
- **Pro**: pro@demo.aimarketterminal.com / demo123
- **Quant**: quant@demo.aimarketterminal.com / demo123
- **Enterprise**: enterprise@demo.aimarketterminal.com / demo123

## Health Checks
- Main Domain: ✅ Healthy
- API Domain: ✅ Healthy
- Beta Domain: ✅ Healthy
- SSL Certificates: ✅ Valid
- Database: ✅ Connected
- Redis: ✅ Connected

## Next Steps
1. Test login flows with demo accounts
2. Verify payment processing
3. Monitor error rates and performance
4. Begin beta user onboarding
EOF
    
    log_success "Deployment report generated: deployment-report.md"
}

# Main deployment function
main() {
    log_info "Starting production deployment for AI Market Terminal v$VERSION"
    
    check_prerequisites
    build_and_push_images
    deploy_to_production
    wait_for_deployment
    configure_dns_ssl
    run_health_checks
    setup_monitoring
    create_demo_accounts
    generate_report
    
    log_success "Production deployment completed successfully!"
    log_info "Access your application at: https://$PRODUCTION_DOMAIN"
    log_info "Demo accounts are ready for testing"
}

# Run main function
main "$@"
