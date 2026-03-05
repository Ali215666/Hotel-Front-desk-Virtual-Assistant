#!/bin/bash
# Quick curl test script for Hotel AI Backend

set -e

BASE_URL="http://localhost:8000"

echo "================================"
echo "Hotel AI Backend - Quick Tests"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/health)
if [ "$STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed (200)${NC}"
else
    echo -e "${RED}✗ Health check failed ($STATUS)${NC}"
    exit 1
fi
echo ""

# Test 2: REST API Chat - First Message
echo -e "${YELLOW}Test 2: REST API - First Message${NC}"
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/chat \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "test123",
        "message": "I want to book a room."
    }')
echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 3: REST API Chat - Follow-up
echo -e "${YELLOW}Test 3: REST API - Follow-up Message${NC}"
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/chat \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "test123",
        "message": "What are your rates?"
    }')
echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 4: Different Session
echo -e "${YELLOW}Test 4: REST API - Different Session${NC}"
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/chat \
    -H "Content-Type: application/json" \
    -d '{
        "session_id": "test456",
        "message": "What time is check-in?"
    }')
echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 5: Error Handling - Missing Field
echo -e "${YELLOW}Test 5: Error Handling - Missing session_id${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${BASE_URL}/api/chat \
    -H "Content-Type: application/json" \
    -d '{
        "message": "Hello"
    }')
if [ "$STATUS" -eq 422 ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid request (422)${NC}"
else
    echo -e "${RED}✗ Expected 422, got $STATUS${NC}"
fi
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "To test WebSocket, use:"
echo "  npm install -g wscat"
echo "  wscat -c ws://localhost:8000/ws/chat"
echo "  Then send: {\"session_id\": \"test\", \"message\": \"Hello\"}"
