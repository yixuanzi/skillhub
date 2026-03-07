# API Key Authentication Design

**Date:** 2025-03-07
**Author:** Claude Code
**Status:** Approved

## Overview

Replace the current tmpkey authentication mechanism with API key authentication. The new authentication flow will support API keys (stored in `api_keys` table) and JWT tokens, with API keys taking precedence.

## Requirements

1. **Remove tmpkey mechanism** - Complete removal of tmpkey-related code
2. **Add API Key authentication** - Integrate into main authentication flow
3. **Authentication order**: API Key → JWT, return first match
4. **API Key format**: Must start with `sk_` prefix
5. **User object**: Must include `auth_type` and `api_key_id` attributes to distinguish authentication source

## Architecture

### Authentication Flow (`core/deps.py`)

```
┌─────────────────────────────────────────────────────────────────┐
│                      get_current_user()                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Extract token from Authorization header                    │
│                                                                 │
│  2. IF token starts with "sk_":                               │
│     └─> APIKeyService.authenticate(db, token)                 │
│         └─> If valid: return user with auth_type="api_key"    │
│                                                                 │
│  3. ELSE try JWT verification:                                │
│     └─> verify_token(token)                                   │
│         └─> If valid: return user with auth_type="jwt"        │
│                                                                 │
│  4. IF both fail: raise HTTPException 401                     │
└─────────────────────────────────────────────────────────────────┘
```

### User Object Attributes

When authenticated via API key, the User object includes:
- `auth_type`: `"api_key"` or `"jwt"`
- `api_key_id`: API key UUID (only for api_key auth)
- `api_key_scopes`: List of scopes (only for api_key auth)

### Database

No changes required to `api_keys` table - existing structure is sufficient:
- `id` - API key UUID
- `user_id` - Associated user
- `key_hash` - SHA-256 hash of the key
- `key_prefix` - First 10 characters
- `scopes` - JSON list of permissions
- `expires_at` - Optional expiration
- `last_used_at` - Last usage timestamp
- `is_active` - Active status

## Files to Modify

| Operation | File Path | Changes |
|-----------|-----------|---------|
| Modify | `core/deps.py` | Update `get_current_user()` to support API key auth |
| Modify | `services/auth_service.py` | Remove tmpkey generation/storage |
| Delete | `core/tmpkey_manager.py` | Entire file |
| Modify | `schemas/auth.py` | Remove `tmpkey` from `TokenResponse` |
| Modify | `api/auth.py` | Remove tmpkey from login response |

## Implementation Notes

1. **API Key format validation**: Check for `sk_` prefix before attempting authentication
2. **Scope preservation**: Pass `api_key_scopes` to request state for endpoint authorization
3. **Backward compatibility**: JWT authentication remains unchanged
4. **Security**: API key hash comparison (never store plaintext keys)

## Testing Considerations

- Test API key authentication (valid key)
- Test API key authentication (invalid key)
- Test API key authentication (expired key)
- Test API key authentication (inactive key)
- Test JWT authentication still works
- Test authentication with malformed tokens
- Test `auth_type` and `api_key_id` attributes are set correctly
