# API Proxy Configuration

## Overview

This project uses Vite's built-in proxy feature to forward API requests from the frontend development server (port 5173) to the backend API server (port 8000). This avoids CORS issues and provides a seamless development experience.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │   Vite Dev      │         │   Backend       │
│   (Browser)     │────────▶│   Server        │────────▶│   API Server    │
│   localhost:5173│         │   Proxy         │         │   localhost:8000│
└─────────────────┘         └─────────────────┘         └─────────────────┘
     API Requests                  Forward                   API Calls
```

## Request Flow

1. **Frontend makes API call**: `axios.get('/api/v1/resources')`
2. **Vite proxy intercepts**: Matches `/api` pattern
3. **Proxy forwards request**: `http://localhost:8000/api/v1/resources`
4. **Backend processes**: FastAPI handles the request
5. **Response returns**: Backend response → Proxy → Frontend

## Configuration Files

### 1. `frontend/.env`
```bash
# Use relative path for development (proxied)
VITE_API_BASE_URL=/api/v1

# For production, use absolute URL:
# VITE_API_BASE_URL=https://api.skillhub.example.com/api/v1
```

### 2. `frontend/vite.config.ts`
```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### 3. `frontend/src/api/client.ts`
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,  // '/api/v1' in development
  // ... configuration
});
```

### 4. `backend/main.py`
```python
# All routers are prefixed with /api/v1
app.include_router(resource_router, prefix="/api/v1")
app.include_router(acl_resource_router, prefix="/api/v1")
```

## API Endpoints

| Feature | Frontend Path | Backend Path |
|---------|--------------|--------------|
| Resources | `/api/v1/resources` | `http://localhost:8000/api/v1/resources` |
| ACL Resources | `/api/v1/acl/resources` | `http://localhost:8000/api/v1/acl/resources` |
| Auth | `/api/v1/auth/*` | `http://localhost:8000/api/v1/auth/*` |

## Development Setup

1. **Start Backend Server** (port 8000):
   ```bash
   cd backend
   python main.py
   ```

2. **Start Frontend Dev Server** (port 5173):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Verify Proxy**: Check the terminal for proxy logs:
   ```
   Proxying: GET /api/v1/resources -> /api/v1/resources
   ```

## Production Deployment

In production, update `.env` to use the actual backend URL:

```bash
VITE_API_BASE_URL=https://api.skillhub.example.com/api/v1
```

Then build and deploy:

```bash
npm run build
# Deploy dist/ folder to your web server
```

## Troubleshooting

### Proxy Not Working
- **Check**: Backend server is running on port 8000
- **Check**: Vite dev server is running on port 5173
- **Check**: No conflicting proxy configurations
- **Check**: Browser console for network errors

### CORS Errors
- **Solution**: Use proxy instead of direct backend access
- **Verify**: `VITE_API_BASE_URL` starts with `/` (relative path)

### 404 Errors
- **Check**: API path includes `/api/v1` prefix
- **Check**: Backend router prefix matches (`/api/v1`)
- **Verify**: Endpoint exists in backend

## Benefits of Using Proxy

1. **No CORS issues**: Same-origin policy is satisfied
2. **Simplified configuration**: No need for absolute URLs
3. **Consistent environment**: Same code in dev and production
4. **Better debugging**: Proxy logs show all API traffic
5. **Security**: Backend URL not exposed in frontend code
