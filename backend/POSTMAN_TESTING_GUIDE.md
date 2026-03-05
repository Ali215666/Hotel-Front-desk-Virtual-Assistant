# Postman Testing Guide for Hotel AI Backend

## 📥 Import Collection into Postman

### Step 1: Import Collection
1. Open Postman
2. Click **Import** button (top left)
3. Drag and drop or browse to:
   - `Hotel_AI_Backend.postman_collection.json`
   - `Hotel_AI_Backend.postman_environment.json` (optional)
4. Click **Import**

### Step 2: Set Environment (Optional)
1. Click the environment dropdown (top right)
2. Select **Hotel AI Backend - Local**
3. Variables are pre-configured for `localhost:8000`

---

## 🧪 Test Collection Overview

### **1. Health & Status** (2 tests)
- ✅ `/health` - Health check endpoint
- ✅ `/` - Root status check

### **2. REST API - /api/chat** (8 tests)
- ✅ Multiple session tests (user123, user456, user789)
- ✅ Follow-up conversation (context retention)
- ✅ Error handling (missing fields, empty messages)
- ✅ Out-of-scope question handling
- ✅ Concurrent user sessions

### **3. WebSocket - /ws/chat**
- 🔌 WebSocket connection instructions
- 📝 Test message templates

### **4. Concurrent Sessions Test** (3 tests)
- ⚡ Tests multiple users simultaneously

---

## 🚀 Quick Start Testing

### Test REST API (Fastest)
1. Ensure backend is running: `python backend/main.py`
2. In Postman, expand **REST API - /api/chat** folder
3. Click **"Chat - Session 1 - Book Room"**
4. Click **Send**
5. Verify response has `reply` field with assistant text

### Test WebSocket (Real-time Streaming)
1. In Postman, click **New** → **WebSocket Request**
2. Enter URL: `ws://localhost:8000/ws/chat`
3. Click **Connect**
4. In message box, paste:
```json
{
    "session_id": "ws_test_1",
    "message": "I want to book a room."
}
```
5. Click **Send**
6. Watch for:
   - Status message: `{"type": "status", "message": "Processing..."}`
   - Streaming text tokens
   - Completion: `{"type": "done", "message": "Response complete"}`

---

## 📋 Example Test Scenarios

### Scenario 1: New Guest Booking
```json
{
    "session_id": "guest001",
    "message": "I want to book a room."
}
```
**Expected**: Welcome message + booking assistance

### Scenario 2: Check Cancellation Policy
```json
{
    "session_id": "guest002",
    "message": "I need to cancel my reservation. What is your cancellation policy?"
}
```
**Expected**: 48-hour cancellation policy details

### Scenario 3: Follow-up in Same Session
**First Message:**
```json
{
    "session_id": "guest003",
    "message": "Do you have any rooms available?"
}
```
**Second Message:**
```json
{
    "session_id": "guest003",
    "message": "What are the prices?"
}
```
**Expected**: Second response uses context from first

### Scenario 4: Out-of-Scope Question
```json
{
    "session_id": "test_scope",
    "message": "What is the capital of France?"
}
```
**Expected**: "I'm sorry, I can only assist with hotel-related inquiries."

---

## ✅ Response Validation

### REST API Response Format
```json
{
    "reply": "string with assistant response"
}
```

### WebSocket Response Types
**Status:**
```json
{"type": "status", "message": "Processing your request..."}
```

**Token Streaming:**
```
Plain text tokens sent individually
```

**Completion:**
```json
{"type": "done", "message": "Response complete"}
```

**Error:**
```json
{"type": "error", "message": "error details"}
```

---

## 🏃 Running Collection Tests

### Run All Tests
1. Click **Collections** in left sidebar
2. Right-click **Hotel Front Desk AI Backend API**
3. Select **Run collection**
4. Click **Run Hotel Front Desk AI Backend API**
5. View results summary

### Run Specific Folder
1. Right-click any folder (e.g., **REST API - /api/chat**)
2. Select **Run folder**
3. Review test results

### Run Tests with Delays (for LLM processing)
1. In Collection Runner
2. Set **Delay** to 2000ms (2 seconds between requests)
3. This prevents overwhelming the LLM

---

## 🔧 Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if needed
cd backend
python main.py
```

### WebSocket Connection Fails
- Ensure backend is running
- Use `ws://` not `wss://` for local testing
- Check firewall settings

### Tests Timing Out
- Increase timeout in Postman settings
- Check if Ollama is running: `ollama list`
- LLM responses can take 5-30 seconds

### Wrong Responses
- Check `backend/logs` for errors
- Verify Ollama model is loaded: `ollama run hotel-qwen`
- Check session isolation (each session_id should be independent)

---

## 📊 Test Assertions Included

All REST API tests include:
- ✅ Status code validation (200, 400, 422, 500)
- ✅ Response structure validation
- ✅ Field type checking
- ✅ Non-empty reply verification
- ✅ Response time checks (< 30s)

WebSocket tests verify:
- ✅ Connection establishment
- ✅ Message format validation
- ✅ Token streaming
- ✅ Completion signals
- ✅ Error handling

---

## 🎯 Expected Test Results

When all tests pass:
- ✅ Health checks: 2/2 passed
- ✅ REST API: 8/8 passed
- ✅ Concurrent sessions: 3/3 passed
- **Total**: 13/13 tests passed

---

## 💡 Tips

1. **Random Session IDs**: Use `{{$randomInt}}` in Postman for unique sessions
2. **Save Responses**: Click **Save Response** to create example responses
3. **Monitor Console**: Check Postman console for detailed request/response logs
4. **Backend Logs**: Watch backend terminal for processing logs
5. **Test Concurrency**: Use Collection Runner with 3-5 iterations simultaneously

---

## 📞 Support

If tests fail:
1. Check backend health: `GET /health`
2. Review backend logs for errors
3. Verify Ollama is running and model is loaded
4. Check network connectivity
5. Ensure all dependencies are installed

Happy Testing! 🚀
