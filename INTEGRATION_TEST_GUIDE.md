# SkillHub Frontend-Backend Integration Verification Guide

## Overview

This guide helps you verify that the frontend authentication is correctly integrated with the backend API.

---

## Quick Start (5 Minutes)

### Step 1: Start Backend

```bash
# Terminal 1
cd ~/Documents/workspace/skillhub

# Initialize and seed database (first time only)
cd backend
python scripts/init_db.py
python scripts/seed_db.py
cd ..

# Start backend server
python -m uvicorn backend.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

### Step 2: Start Frontend

```bash
# Terminal 2
cd ~/Documents/workspace/skillhub/frontend

# Install dependencies (first time only)
npm install

# Start frontend
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 3: Test Authentication

1. **Open Browser**: `http://localhost:5173`

2. **Register New User**:
   - Click "Request Access"
   - Fill in:
     - Username: `testuser`
     - Email: `test@example.com`
     - Password: `Test1234` (must be 8+ chars)
     - Confirm: `Test1234`
   - Click "Request Access"
   - ✅ Should redirect to login page

3. **Login**:
   - Use the newly created user or default admin:
     - Username: `admin`
     - Password: `admin123`
   - Click "Access System"
   - ✅ Should redirect to dashboard

4. **Verify Token Storage**:
   - Open DevTools → Application → Local Storage
   - ✅ Should see `access_token` and `refresh_token`

---

## Detailed API Testing

### Option A: Automated Script

```bash
cd ~/Documents/workspace/skillhub
./backend/test_api_quick.sh
```

### Option B: Manual curl Commands

```bash
# Set base URL
export BASE_URL="http://localhost:8000/api/v1"

# 1. Health Check
curl http://localhost:8000/health

# 2. Register User
curl -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test1234"
  }'

# 3. Login
export TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 4. Access Protected Endpoint
curl -X GET $BASE_URL/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integration Points Verified

### ✅ Backend API

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/health` | GET | ✅ | Health check |
| `/api/v1/auth/register` | POST | ✅ | User registration |
| `/api/v1/auth/login` | POST | ✅ | Returns JWT tokens |
| `/api/v1/auth/refresh` | POST | ✅ | Token refresh |
| `/api/v1/auth/logout` | POST | ✅ | Invalidate token |
| `/api/v1/auth/me` | GET | ✅ | Get current user |

### ✅ Frontend Integration

| Feature | Status | Notes |
|---------|--------|-------|
| API Client | ✅ | Axios with interceptors |
| Token Storage | ✅ | localStorage |
| Auto Refresh | ✅ | On 401 response |
| Request Headers | ✅ | `Bearer <token>` |
| Error Handling | ✅ | Extracts `detail` from errors |
| Route Protection | ✅ | Auth guards in App.tsx |

---

## Response Format Mappings

### Login Response

**Backend returns:**
```json
{
  "access_token": "a1b2c3d4e5f6... (32 chars)",
  "refresh_token": "x9y8z7w6v5u4... (32 chars)",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Frontend expects:**
```javascript
{
  access_token: string,
  refresh_token: string,
  token_type: string,
  expires_in: number
}
```

### User Response

**Backend returns:**
```json
{
  "id": "uuid",
  "username": "admin",
  "email": "admin@skillhub.local",
  "is_active": true,
  "created_at": "2025-02-28T..."
}
```

**Frontend maps to:**
```typescript
{
  id: string,
  username: string,
  email: string,
  roles: Role[],
  createdAt: string,
  updatedAt: string
}
```

### Error Response

**Backend returns (FastAPI default):**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Frontend extracts:**
```typescript
axiosError.response?.data?.detail || "Login failed"
```

---

## Key Configuration Files

### Backend

**`backend/main.py`:**
```python
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**`backend/api/auth.py`:**
```python
router = APIRouter(prefix="/auth", tags=["Authentication"])
# Routes: /register, /login, /refresh, /logout, /me
```

### Frontend

**`frontend/vite.config.ts`:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

**`frontend/src/api/client.ts`:**
```typescript
// Request Interceptor: Adds Authorization header
// Response Interceptor: Handles 401 and refresh
```

**`frontend/.env`:**
```env
VITE_API_BASE_URL=/api/v1
```

---

## Troubleshooting

### Problem: "Network Error"

**Cause:** Backend not running

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it:
python -m uvicorn backend.main:app --reload --port 8000
```

---

### Problem: "CORS Error"

**Cause:** CORS not configured

**Solution:**
Check `backend/main.py` has:
```python
allow_origins=["http://localhost:5173"]
```

---

### Problem: "401 Unauthorized" on login

**Cause:** Wrong password or user doesn't exist

**Solution:**
```bash
# Create admin user
python backend/scripts/seed_db.py

# Then login with: admin / admin123
```

---

### Problem: "401 on subsequent requests"

**Cause:** Token not stored or invalid header format

**Solution:**
```javascript
// Check DevTools Console:
localStorage.getItem('access_token')

// Check Network tab for Authorization header:
// Should be: "Bearer <token>"
```

---

### Problem: "Database error"

**Cause:** Database not initialized

**Solution:**
```bash
cd backend
python scripts/init_db.py
python scripts/seed_db.py
```

---

## Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can register new user
- [ ] Can login with admin/admin123
- [ ] Tokens stored in localStorage
- [ ] Dashboard loads after login
- [ ] Can logout
- [ ] Tokens cleared after logout

---

## Next Steps

Once authentication is verified:

1. **Skills API**: Implement skills CRUD endpoints
2. **Users API**: Implement user management endpoints
3. **ACL API**: Implement access control endpoints
4. **Gateway**: Implement unified API gateway

---

## Files Modified for Integration

### Backend (already implemented)
- ✅ `backend/api/auth.py` - Auth endpoints
- ✅ `backend/services/auth_service.py` - Auth logic
- ✅ `backend/schemas/auth.py` - Request/response schemas
- ✅ `backend/core/security.py` - JWT and password hashing
- ✅ `backend/main.py` - App setup with CORS

### Frontend (modified for integration)
- ✅ `frontend/src/api/auth.ts` - Updated response types
- ✅ `frontend/src/api/client.ts` - Fixed refresh token handling
- ✅ `frontend/src/hooks/useAuth.ts` - Updated to match backend
- ✅ `frontend/src/pages/auth/LoginPage.tsx` - Better error handling
- ✅ `frontend/src/pages/auth/RegisterPage.tsx` - Better error handling

---

**Last Updated**: 2025-02-28
**Status**: ✅ Ready for Testing
