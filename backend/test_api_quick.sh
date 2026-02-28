#!/bin/bash

# Quick API Test Script
# Tests the authentication endpoints

BASE_URL="http://localhost:8000/api/v1"

echo "========================================="
echo "SkillHub Backend API Test"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
echo "GET /health"
response=$(curl -s http://localhost:8000/health)
if [[ $response == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Response: $response"
    exit 1
fi
echo ""

# Test 2: Register User
echo -e "${YELLOW}Test 2: Register New User${NC}"
echo "POST /auth/register"
response=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "email": "test'$RANDOM'@example.com",
    "password": "Test1234"
  }')

if [[ $response == *"username"* ]] && [[ $response == *"id"* ]]; then
    echo -e "${GREEN}✓ User registered successfully${NC}"
    username=$(echo $response | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "Username: $username"
else
    echo -e "${RED}✗ Registration failed${NC}"
    echo "Response: $response"
fi
echo ""

# Test 3: Login (with test user)
echo -e "${YELLOW}Test 3: Login${NC}"
echo "POST /auth/login"
response=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

if [[ $response == *"access_token"* ]]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    access_token=$(echo $response | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    refresh_token=$(echo $response | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)
    echo "Access Token: ${access_token:0:20}..."
    echo "Refresh Token: ${refresh_token:0:20}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "Response: $response"
    echo -e "${YELLOW}Note: Make sure you have run seed_db.py to create the admin user${NC}"
fi
echo ""

# Test 4: Get Current User
if [[ -n "$access_token" ]]; then
    echo -e "${YELLOW}Test 4: Get Current User (Protected)${NC}"
    echo "GET /auth/me"
    response=$(curl -s -X GET $BASE_URL/auth/me \
      -H "Authorization: Bearer $access_token")

    if [[ $response == *"username"* ]] && [[ $response == *"email"* ]]; then
        echo -e "${GREEN}✓ Protected endpoint accessible${NC}"
        echo "Response: $response"
    else
        echo -e "${RED}✗ Protected endpoint failed${NC}"
        echo "Response: $response"
    fi
    echo ""

    # Test 5: Token Refresh
    echo -e "${YELLOW}Test 5: Refresh Token${NC}"
    echo "POST /auth/refresh"
    response=$(curl -s -X POST $BASE_URL/auth/refresh \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\": \"$refresh_token\"}")

    if [[ $response == *"access_token"* ]]; then
        echo -e "${GREEN}✓ Token refreshed successfully${NC}"
        new_access_token=$(echo $response | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        echo "New Access Token: ${new_access_token:0:20}..."
    else
        echo -e "${RED}✗ Token refresh failed${NC}"
        echo "Response: $response"
    fi
    echo ""

    # Test 6: Logout
    echo -e "${YELLOW}Test 6: Logout${NC}"
    echo "POST /auth/logout"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $BASE_URL/auth/logout \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\": \"$refresh_token\"}")
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d':' -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')

    if [[ "$http_code" == "204" ]]; then
        echo -e "${GREEN}✓ Logout successful${NC}"
    else
        echo -e "${RED}✗ Logout failed${NC}"
        echo "HTTP Code: $http_code"
        echo "Response: $body"
    fi
else
    echo -e "${YELLOW}Skipping remaining tests (no access token)${NC}"
fi

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Make sure the backend is running on port 8000"
echo -e "Run: ${GREEN}python -m uvicorn backend.main:app --reload --port 8000${NC}"
echo ""
