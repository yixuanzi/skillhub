# Audit Logs

This guide covers how to view, filter, and understand audit logs in SkillHub.

## Overview

Audit logs provide a comprehensive record of all system actions for:

- **Security monitoring**: Track suspicious activity
- **Compliance**: Meet audit requirements
- **Debugging**: Investigate issues
- **Analytics**: Understand system usage

All HTTP requests and significant actions are automatically logged.

## What Gets Logged

### System Actions

| Action | Description |
|--------|-------------|
| `login` | User login |
| `logout` | User logout |
| `login_failed` | Failed login attempt |
| `resource.create` | Gateway resource created |
| `resource.update` | Gateway resource updated |
| `resource.delete` | Gateway resource deleted |
| `resource.read` | Gateway resource accessed |
| `skill.call` | Skill invoked |
| `skill.create` | Skill created |
| `skill.update` | Skill updated |
| `skill.delete` | Skill deleted |
| `acl.create` | ACL rule created |
| `acl.update` | ACL rule updated |
| `acl.delete` | ACL rule deleted |
| `acl.check_permission` | Permission check performed |
| `api_key.create` | API key created |
| `api_key.update` | API key updated |
| `api_key.delete` | API key revoked |
| `api_key.rotate` | API key rotated |
| `api_key.use` | API key used for authentication |
| `user.create` | User created |
| `user.update` | User updated |
| `user.delete` | User deleted |
| `user.role_assign` | Role assigned to user |
| `token.create` | Token stored |
| `token.update` | Token updated |
| `token.delete` | Token deleted |
| `gateway.request` | Gateway API request |
| `gateway.proxy` | Gateway proxied request |

### HTTP Requests

Every HTTP request is logged with:
- Method and path
- Query parameters
- Response status code
- Request duration
- Authentication method
- User ID (if authenticated)
- IP address
- User agent

## Viewing Audit Logs

### Via Web UI

1. Navigate to **Settings** → **Audit Logs** (admin only)
2. Use filters to narrow results:
   - **Action**: Filter by action type
   - **Resource Type**: Filter by resource (user, skill, etc.)
   - **User ID**: Filter by specific user
   - **Date Range**: Filter by date range
   - **Status**: Filter by success/failure
3. Click on any log entry to see full details

### Via API

**Note**: Audit log access requires admin role.

List audit logs:
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

With filters:
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?action=api_key.create&status=success&start_date=2026-03-01T00:00:00Z" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

Get specific log entry:
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/{log_id}/" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Response Format

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "user-uuid",
      "action": "api_key.create",
      "resource_type": "api_key",
      "resource_id": "key-uuid",
      "details": {
        "key_name": "Production Key",
        "scopes": ["skills:call"]
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "status": "success",
      "error_message": null,
      "created_at": "2026-03-06T10:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20
}
```

## Filter Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (starts at 1) |
| `size` | integer | Items per page (max 100) |
| `action` | string | Filter by action type |
| `resource_type` | string | Filter by resource type |
| `user_id` | string | Filter by user ID |
| `status` | string | Filter by status (success/failure) |
| `start_date` | datetime | Filter by start date |
| `end_date` | datetime | Filter by end date |

## Data Retention

Audit logs are retained based on the `AUDIT_LOG_RETENTION_DAYS` setting:

| Setting | Default | Description |
|---------|---------|-------------|
| `AUDIT_LOG_RETENTION_DAYS` | 90 | Number of days to retain logs |

Logs older than the retention period should be archived or deleted via a scheduled job.

## Sensitive Data Handling

Certain fields are automatically redacted from audit logs to prevent sensitive data exposure:

- Passwords
- Tokens
- Secrets

Configure sensitive fields via environment variable:
```
AUDIT_LOG_SENSITIVE_FIELDS=password,token,secret,api_key
```

## Performance Considerations

### Async Logging

Audit logging can be configured to run asynchronously to avoid impacting request performance:

```bash
AUDIT_LOG_ASYNC=true
```

When enabled, logs are written to a queue and processed in the background.

### Excluded Paths

Certain paths are excluded from audit logging to reduce noise:
- `/health` - Health check endpoint
- `/` - Root endpoint
- `/docs` - API documentation
- `/openapi.json` - OpenAPI schema
- `/redoc` - ReDoc documentation

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_LOG_ENABLED` | `true` | Enable/disable audit logging |
| `AUDIT_LOG_RETENTION_DAYS` | `90` | Days to retain logs |
| `AUDIT_LOG_ASYNC` | `true` | Use async logging |
| `AUDIT_LOG_SENSITIVE_FIELDS` | `password,token,secret` | Fields to redact |

## Security

### Access Control

- **Admin-only**: Only users with the `admin` role can view audit logs
- **Immutable**: Logs cannot be modified after creation
- **Comprehensive**: All actions are logged, including failed attempts

### Monitoring Recommendations

1. **Regular review**: Review logs weekly for suspicious activity
2. **Alerts**: Set up alerts for:
   - Multiple failed login attempts from same IP
   - Access from unusual geographic locations
   - Actions performed outside business hours
   - Unusual resource access patterns

3. **Audit the auditors**: Log who accesses the audit logs

## Example Queries

### Find all failed logins
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?action=login_failed&start_date=2026-03-01T00:00:00Z" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Find all skill calls by a user
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?action=skill.call&user_id={user_id}" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Find all API key creations
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?action=api_key.create" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Find errors in a date range
```bash
curl -X GET "https://api.skillhub.com/api/v1/audit-logs/?status=failure&start_date=2026-03-01T00:00:00Z&end_date=2026-03-07T23:59:59Z" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```
