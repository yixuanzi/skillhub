# API Keys

This guide covers how to create, use, and manage API keys in SkillHub.

## Overview

API keys provide programmatic access to the SkillHub API without requiring interactive authentication. Each API key is:

- **User-scoped**: Belongs to a specific user
- **Secure**: SHA256 hashed, only shown once during creation
- **Scoped**: Limited to specific permissions based on configured scopes
- **Revocable**: Can be deactivated at any time
- **Rotatable**: Can be regenerated without changing settings

## Creating an API Key

### Via Web UI

1. Navigate to **Settings** → **API Keys**
2. Click **Create New Key**
3. Enter a name for the key (e.g., "Production Integration")
4. Select the required scopes (permissions)
5. Optionally set an expiration date
6. Click **Create**
7. **Copy the key immediately** - it won't be shown again!

### Via API

```bash
curl -X POST "https://api.skillhub.com/api/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Integration",
    "scopes": ["skills:call", "skills:read"],
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

Response (includes full key - shown only once):
```json
{
  "key": "sk_abc123...",
  "api_key": {
    "id": "uuid",
    "name": "My Integration",
    "key_prefix": "sk_abc123",
    "scopes": ["skills:call", "skills:read"],
    "expires_at": "2026-12-31T23:59:59Z",
    "last_used_at": null,
    "is_active": true,
    "created_at": "2026-03-06T00:00:00Z"
  }
}
```

## Using an API Key

Include the API key in the `Authorization` header as a Bearer token:

```bash
curl -X GET "https://api.skillhub.com/api/v1/skills/" \
  -H "Authorization: Bearer sk_abc123..."
```

The API key format is: `sk_` followed by 43 characters (URL-safe base64).

## Available Scopes

| Scope | Description |
|-------|-------------|
| `resources:read` | Read gateway resources |
| `resources:write` | Create/modify gateway resources |
| `skills:read` | View skills |
| `skills:call` | Execute/invoke skills |
| `skills:write` | Create/modify skills |
| `acl:read` | View ACL rules |
| `acl:write` | Create/modify ACL rules |
| `tokens:read` | View stored tokens |
| `tokens:write` | Create/modify stored tokens |

## Security Best Practices

### 1. Store Keys Securely
- Never commit API keys to version control
- Use environment variables or secret management systems
- Consider using a `.env` file (add to `.gitignore`)

### 2. Principle of Least Privilege
- Only grant scopes that are actually needed
- Create separate keys for different environments (dev, staging, prod)
- Use read-only scopes when write access isn't required

### 3. Key Rotation
- Rotate keys regularly (recommended: every 90 days)
- Rotate immediately if a key is suspected to be compromised
- Use the rotate endpoint to generate a new key without changing settings

### 4. Monitoring
- Monitor the `last_used_at` timestamp to detect unused keys
- Revoke keys that are no longer needed
- Check audit logs for suspicious activity

### 5. Expiration
- Set expiration dates for keys with temporary access needs
- Avoid permanent keys for one-time operations

## Managing API Keys

### List Your Keys

```bash
curl -X GET "https://api.skillhub.com/api/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update a Key

```bash
curl -X PUT "https://api.skillhub.com/api/v1/api-keys/{key_id}/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "scopes": ["skills:call"],
    "expires_at": "2026-06-30T23:59:59Z"
  }'
```

### Rotate a Key

```bash
curl -X POST "https://api.skillhub.com/api/v1/api-keys/{key_id}/rotate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

This invalidates the old key and returns a new one.

### Revoke a Key

```bash
curl -X DELETE "https://api.skillhub.com/api/v1/api-keys/{key_id}/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Limits

- **Maximum active keys per user**: 100
- **Key format**: `sk_` + 43 characters
- **Hashing algorithm**: SHA256

## Error Handling

| HTTP Code | Description |
|-----------|-------------|
| 401 | Invalid or expired API key |
| 403 | API key missing required scope |
| 404 | API key not found |
| 400 | Validation error (e.g., invalid scopes) |

Example error response:
```json
{
  "detail": "API key missing required scope: skills:call"
}
```

## Environment Configuration

Configure API key behavior via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY_MAX_PER_USER` | 100 | Maximum active keys per user |
| `API_KEY_DEFAULT_EXPIRATION_DAYS` | 365 | Default expiration for new keys |
| `API_KEY_PREFIX` | `sk_` | Prefix for all API keys |
