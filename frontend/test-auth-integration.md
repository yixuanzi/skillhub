# Frontend-Backend Auth Integration Test

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Database initialized with test data

## Setup Backend

```bash
# 1. Install dependencies (if not already done)
cd backend
pip install -r requirements.txt

# 2. Initialize database
python scripts/init_db.py

# 3. (Optional) Seed with test data
python scripts/seed_db.py

# 4. Start backend server
cd ..
python -m uvicorn backend.main:app --reload --port 8000
```

## Setup Frontend

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Start frontend dev server
npm run dev
```

## Manual Test Cases

### Test 1: Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status": "healthy"}
```

### Test 2: Register New User

**Frontend:**
1. Navigate to `http://localhost:5173/register`
2. Fill in:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `Test1234`
   - Confirm Password: `Test1234`
3. Click "Request Access"
4. Should redirect to login page

**Or via curl:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test1234"
  }'
```

Expected response:
```json
{
  "id": "...",
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2025-02-28T..."
}
```

### Test 3: Login

**Frontend:**
1. Navigate to `http://localhost:5173/login`
2. Enter credentials:
   - Username: `testuser`
   - Password: `Test1234`
3. Click "Access System"
4. Should redirect to dashboard

**Or via curl:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test1234"
  }'
```

Expected response:
```json
{
  "access_token": "...32 chars...",
  "refresh_token": "...32 chars...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Test 4: Access Protected Endpoint

**Via curl:**
```bash
# Store the access_token from Test 3
ACCESS_TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected response:
```json
{
  "id": "...",
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "..."
}
```

### Test 5: Token Refresh

**Via curl:**
```bash
# Store the refresh_token from Test 3
REFRESH_TOKEN="your_refresh_token_here"

curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "'"$REFRESH_TOKEN"'"
  }'
```

Expected response:
```json
{
  "access_token": "...new token...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Test 6: Logout

**Via curl:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "'"$REFRESH_TOKEN"'"
  }'
```

Expected: 204 No Content

## Frontend Integration Checklist

- [ ] Register page submits successfully
- [ ] After registration, redirects to login
- [ ] Login page accepts credentials
- [ ] After login, redirects to dashboard
- [ ] Dashboard shows user info (if implemented)
- [ ] Token stored in localStorage as `access_token`
- [ ] Refresh token stored as `refresh_token`
- [ ] API requests include `Authorization: Bearer <token>` header
- [ ] 401 errors trigger token refresh
- [ ] Logout clears tokens and redirects to login

## Troubleshooting

### CORS Errors

**Error:** "Access-Control-Allow-Origin header is missing"

**Solution:** Check backend CORS settings in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Network Errors

**Error:** "Network Error" or "ERR_CONNECTION_REFUSED"

**Solution:**
- Verify backend is running on port 8000
- Check frontend proxy configuration in `vite.config.ts`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

### 401 Unauthorized

**Error:** Login succeeds but subsequent requests return 401

**Solution:**
- Check browser console for token storage
- Verify `Authorization` header format: `Bearer <token>`
- Ensure backend token validation works

### Database Errors

**Error:** "Table 'users' doesn't exist"

**Solution:**
```bash
cd backend
python scripts/init_db.py
```

## API Endpoint Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Invalidate refresh token | No |
| GET | `/api/v1/auth/me` | Get current user | Yes |

## Data Flow

1. **Registration:**
   ```
   Frontend → POST /auth/register → Backend
   ← User Response ←
   Navigate to /login
   ```

2. **Login:**
   ```
   Frontend → POST /auth/login → Backend
   ← Token Response ←
   Store tokens in localStorage
   Update auth store
   Navigate to /dashboard
   ```

3. **API Request:**
   ```
   Frontend → API Request (with Bearer token) → Backend
   ← Response ←
   ```

4. **Token Refresh (auto on 401):**
   ```
   Frontend ← 401 Error ← Backend
   → POST /auth/refresh → Backend
   ← New access_token ←
   Retry original request
   ```

5. **Logout:**
   ```
   Frontend → POST /auth/logout (with refresh_token) → Backend
   Clear localStorage
   Clear auth store
   Navigate to /login
   ```
