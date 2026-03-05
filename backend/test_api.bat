@echo off
REM Quick curl test script for Hotel AI Backend (Windows)

SET BASE_URL=http://localhost:8000

echo ================================
echo Hotel AI Backend - Quick Tests
echo ================================
echo.

REM Test 1: Health Check
echo Test 1: Health Check
curl -s -o nul -w "Status: %%{http_code}" %BASE_URL%/health
echo.
echo.

REM Test 2: REST API Chat - First Message
echo Test 2: REST API - First Message
curl -X POST %BASE_URL%/api/chat ^
    -H "Content-Type: application/json" ^
    -d "{\"session_id\": \"test123\", \"message\": \"I want to book a room.\"}"
echo.
echo.

REM Test 3: REST API Chat - Follow-up
echo Test 3: REST API - Follow-up Message
curl -X POST %BASE_URL%/api/chat ^
    -H "Content-Type: application/json" ^
    -d "{\"session_id\": \"test123\", \"message\": \"What are your rates?\"}"
echo.
echo.

REM Test 4: Different Session
echo Test 4: REST API - Different Session
curl -X POST %BASE_URL%/api/chat ^
    -H "Content-Type: application/json" ^
    -d "{\"session_id\": \"test456\", \"message\": \"What time is check-in?\"}"
echo.
echo.

REM Test 5: Error Handling
echo Test 5: Error Handling - Missing session_id
curl -X POST %BASE_URL%/api/chat ^
    -H "Content-Type: application/json" ^
    -d "{\"message\": \"Hello\"}"
echo.
echo.

echo ================================
echo All tests completed!
echo ================================
echo.
echo To test WebSocket, install wscat:
echo   npm install -g wscat
echo   wscat -c ws://localhost:8000/ws/chat
echo   Then send: {"session_id": "test", "message": "Hello"}
