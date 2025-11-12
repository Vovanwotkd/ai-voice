#!/bin/bash

# AI Voice Hostess Bot - API Integration Test Script
# Usage: ./test_api.sh [backend_url]
# Example: ./test_api.sh http://localhost:8000

set -e

BACKEND_URL="${1:-http://localhost:8000}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "==========================================="
echo "🧪 AI Voice Hostess Bot - API Tests"
echo "==========================================="
echo "Backend URL: $BACKEND_URL"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"

    echo -n "Testing: $test_name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "   Response: $(echo $body | head -c 100)..."
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "   Response: $body"
    fi
    echo ""
}

# Test 1: Root endpoint
run_test "Root endpoint" "$BACKEND_URL/"

# Test 2: Health check
run_test "Health check" "$BACKEND_URL/api/health"

# Test 3: Database health check
run_test "Database health check" "$BACKEND_URL/api/health/db"

# Test 4: Get all prompts
run_test "Get all prompts" "$BACKEND_URL/api/prompts/"

# Test 5: Get active prompt
run_test "Get active prompt" "$BACKEND_URL/api/prompts/active"

# Test 6: Get available variables
run_test "Get available variables" "$BACKEND_URL/api/prompts/variables/available"

# Test 7: Send chat message
echo -e "${YELLOW}Testing chat message (may take 2-5 seconds for LLM response)...${NC}"
chat_data='{
  "message": "Здравствуйте, хочу забронировать столик на двоих",
  "conversation_id": null,
  "generate_audio": false
}'
run_test "Send chat message" "$BACKEND_URL/api/chat/message" "POST" "$chat_data"

# Test 8: Get chat history
run_test "Get chat history" "$BACKEND_URL/api/chat/history?limit=10&offset=0"

# Test 9: Preview prompt
preview_data='{
  "content": "Привет! Я работаю в {restaurant_name}. Дата: {date}"
}'
run_test "Preview prompt" "$BACKEND_URL/api/prompts/preview" "POST" "$preview_data"

# Test 10: Hot reload prompts
run_test "Hot reload prompts" "$BACKEND_URL/api/prompts/reload" "POST" ""

# Summary
echo "==========================================="
echo "📊 Test Summary"
echo "==========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
    exit 1
fi
