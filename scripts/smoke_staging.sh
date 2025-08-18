#!/bin/bash

# Smoke Tests for AI Market Terminal Staging
# Automated tests to verify staging deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STAGING_URL="https://staging.aimarketterminal.com"
API_URL="https://api.staging.aimarketterminal.com"
TEST_USER_EMAIL="smoke-test@aimarketterminal.com"
TEST_USER_PASSWORD="smoke_test_password_2024"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_failure() {
    echo -e "${RED}[FAILURE]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# HTTP request helper
http_request() {
    local method=$1
    local url=$2
    local data=$3
    local headers=$4
    
    if [ -n "$data" ]; then
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" -H "$headers" -d "$data"
        else
            curl -s -X "$method" "$url" -d "$data"
        fi
    else
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" -H "$headers"
        else
            curl -s -X "$method" "$url"
        fi
    fi
}

# Test health endpoint
test_health() {
    log_info "Testing health endpoint..."
    
    response=$(http_request "GET" "$API_URL/health")
    if echo "$response" | grep -q '"status":"healthy"'; then
        log_success "Health check passed"
    else
        log_failure "Health check failed: $response"
    fi
}

# Test user registration
test_user_registration() {
    log_info "Testing user registration..."
    
    data='{"email":"'$TEST_USER_EMAIL'","password":"'$TEST_USER_PASSWORD'"}'
    response=$(http_request "POST" "$API_URL/auth/signup" "$data" "Content-Type: application/json")
    
    if echo "$response" | grep -q '"access_token"'; then
        log_success "User registration passed"
        # Extract token for subsequent tests
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        log_failure "User registration failed: $response"
    fi
}

# Test user login
test_user_login() {
    log_info "Testing user login..."
    
    data='{"email":"'$TEST_USER_EMAIL'","password":"'$TEST_USER_PASSWORD'"}'
    response=$(http_request "POST" "$API_URL/auth/login" "$data" "Content-Type: application/json")
    
    if echo "$response" | grep -q '"access_token"'; then
        log_success "User login passed"
        # Extract token for subsequent tests
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        log_failure "User login failed: $response"
    fi
}

# Test user profile
test_user_profile() {
    log_info "Testing user profile..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for profile test"
        return
    fi
    
    response=$(http_request "GET" "$API_URL/user/profile" "" "Authorization: Bearer $TOKEN")
    
    if echo "$response" | grep -q '"email":"'$TEST_USER_EMAIL'"'; then
        log_success "User profile test passed"
    else
        log_failure "User profile test failed: $response"
    fi
}

# Test AI tutor
test_ai_tutor() {
    log_info "Testing AI tutor..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for AI tutor test"
        return
    fi
    
    data='{"question":"What is a stock?"}'
    response=$(http_request "POST" "$API_URL/learn/ask" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"answer"'; then
        log_success "AI tutor test passed"
    else
        log_failure "AI tutor test failed: $response"
    fi
}

# Test market research
test_market_research() {
    log_info "Testing market research..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for market research test"
        return
    fi
    
    response=$(http_request "GET" "$API_URL/research?ticker=AAPL&range=1mo" "" "Authorization: Bearer $TOKEN")
    
    if echo "$response" | grep -q '"symbol":"AAPL"'; then
        log_success "Market research test passed"
    else
        log_failure "Market research test failed: $response"
    fi
}

# Test AI strategy generation
test_ai_strategy() {
    log_info "Testing AI strategy generation..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for AI strategy test"
        return
    fi
    
    data='{"description":"SMA on AAPL daily"}'
    response=$(http_request "POST" "$API_URL/strategy/ai" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"strategy"'; then
        log_success "AI strategy test passed"
        # Extract strategy parameters for backtest
        STRATEGY_PARAMS=$(echo "$response" | grep -o '"parameters":{[^}]*}')
    else
        log_failure "AI strategy test failed: $response"
    fi
}

# Test backtest execution
test_backtest() {
    log_info "Testing backtest execution..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for backtest test"
        return
    fi
    
    data='{"symbol":"AAPL","strategy":"SMA","start_date":"2024-01-01","end_date":"2024-12-01","initial_capital":10000}'
    response=$(http_request "POST" "$API_URL/backtest" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"total_return"'; then
        log_success "Backtest test passed"
        BACKTEST_ID=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    else
        log_failure "Backtest test failed: $response"
    fi
}

# Test paper trading
test_paper_trading() {
    log_info "Testing paper trading..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for paper trading test"
        return
    fi
    
    data='{"symbol":"AAPL","side":"buy","quantity":10,"price":150.00}'
    response=$(http_request "POST" "$API_URL/trading/paper-trade" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"status":"executed"'; then
        log_success "Paper trading test passed"
    else
        log_failure "Paper trading test failed: $response"
    fi
}

# Test live trading (should be gated for Pro+)
test_live_trading() {
    log_info "Testing live trading (should be gated)..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for live trading test"
        return
    fi
    
    data='{"symbol":"AAPL","side":"buy","quantity":10,"price":150.00}'
    response=$(http_request "POST" "$API_URL/trading/live-trade" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"detail"'; then
        log_success "Live trading gating test passed (correctly blocked)"
    else
        log_failure "Live trading gating test failed: should be blocked for Learner tier"
    fi
}

# Test Stripe upgrade flow
test_stripe_upgrade() {
    log_info "Testing Stripe upgrade flow..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for Stripe upgrade test"
        return
    fi
    
    data='{"tier":"pro"}'
    response=$(http_request "POST" "$API_URL/billing/checkout" "$data" "Authorization: Bearer $TOKEN; Content-Type: application/json")
    
    if echo "$response" | grep -q '"checkout_url"'; then
        log_success "Stripe checkout creation test passed"
    else
        log_failure "Stripe checkout creation test failed: $response"
    fi
}

# Test billing portal
test_billing_portal() {
    log_info "Testing billing portal..."
    
    if [ -z "$TOKEN" ]; then
        log_failure "No token available for billing portal test"
        return
    fi
    
    response=$(http_request "POST" "$API_URL/billing/portal" "" "Authorization: Bearer $TOKEN")
    
    if echo "$response" | grep -q '"portal_url"'; then
        log_success "Billing portal test passed"
    else
        log_failure "Billing portal test failed: $response"
    fi
}

# Test web application
test_web_application() {
    log_info "Testing web application..."
    
    response=$(http_request "GET" "$STAGING_URL/")
    
    if echo "$response" | grep -q "AI Market Terminal"; then
        log_success "Web application test passed"
    else
        log_failure "Web application test failed"
    fi
}

# Test API documentation
test_api_docs() {
    log_info "Testing API documentation..."
    
    response=$(http_request "GET" "$API_URL/docs")
    
    if echo "$response" | grep -q "Swagger UI"; then
        log_success "API documentation test passed"
    else
        log_failure "API documentation test failed"
    fi
}

# Test metrics endpoint
test_metrics() {
    log_info "Testing metrics endpoint..."
    
    response=$(http_request "GET" "$API_URL/metrics")
    
    if echo "$response" | grep -q "http_requests_total"; then
        log_success "Metrics endpoint test passed"
    else
        log_failure "Metrics endpoint test failed"
    fi
}

# Cleanup test user
cleanup_test_user() {
    log_info "Cleaning up test user..."
    
    if [ -n "$TOKEN" ]; then
        response=$(http_request "DELETE" "$API_URL/user/profile" "" "Authorization: Bearer $TOKEN")
        if echo "$response" | grep -q '"message"'; then
            log_success "Test user cleanup completed"
        else
            log_warning "Test user cleanup failed: $response"
        fi
    fi
}

# Generate test report
generate_report() {
    echo ""
    echo "📊 SMOKE TEST REPORT"
    echo "==================="
    echo "✅ Tests Passed: $TESTS_PASSED"
    echo "❌ Tests Failed: $TESTS_FAILED"
    echo "📊 Success Rate: $((TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED)))%"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo "🎉 ALL SMOKE TESTS PASSED!"
        echo "Staging environment is ready for beta testing."
        return 0
    else
        echo "⚠️  SOME TESTS FAILED!"
        echo "Please investigate and fix the issues before proceeding."
        return 1
    fi
}

# Main test execution
main() {
    echo "🚀 Starting AI Market Terminal Smoke Tests"
    echo "=========================================="
    echo "Staging URL: $STAGING_URL"
    echo "API URL: $API_URL"
    echo ""
    
    # Run all tests
    test_health
    test_web_application
    test_api_docs
    test_metrics
    test_user_registration
    test_user_login
    test_user_profile
    test_ai_tutor
    test_market_research
    test_ai_strategy
    test_backtest
    test_paper_trading
    test_live_trading
    test_stripe_upgrade
    test_billing_portal
    
    # Cleanup
    cleanup_test_user
    
    # Generate report
    generate_report
}

# Run main function
main "$@"
