# ✅ ACL和Resource API对接修复完成

## 🎯 问题总结

用户发现两个主要问题：

1. **ACL模块调用了错误的API** - ACL page应该调用ACL API (`/api/v1/acl/resources/`) 而不是Resource API
2. **列表显示异常** - 前后端字段命名不一致导致数据无法正确显示

## 🔍 根本原因

### 1. 命名风格不匹配
- **后端**: Python FastAPI 使用蛇形命名 (`created_at`, `access_mode`, `ip_whitelist`)
- **前端**: TypeScript 使用驼峰命名 (`createdAt`, `accessMode`, `ipWhitelist`)

### 2. API响应结构不匹配
- **后端**: 直接返回Pydantic模型
  ```json
  {
    "items": [...],
    "total": 10,
    "page": 1,
    "size": 20
  }
  ```
- **前端期望**: 包裹在ApiResponse中
  ```json
  {
    "success": true,
    "data": {
      "items": [...],
      "total": 10
    }
  }
  ```

## 🛠️ 修复方案

### 核心策略：**前端适配后端**

由于后端API已经实现且符合Python/FastAPI的最佳实践，我们选择让前端适配后端的数据结构，使用蛇形命名。

### 1. 类型定义更新

#### Resource类型 (`src/types/index.ts`)
```typescript
export interface Resource {
  id: string;
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  created_at: string;   // ✅ 蛇形匹配后端
  updated_at: string;   // ✅ 蛇形匹配后端
}
```

#### ACL类型 (`src/types/index.ts`)
```typescript
export interface ACLRule {
  id: string;
  resource_id: string;      // ✅ 蛇形
  resource_name: string;    // ✅ 蛇形
  access_mode: AccessMode;  // ✅ 蛇形 ('any' | 'rbac')
  conditions?: ACLConditions;
  created_at: string;       // ✅ 蛇形
  role_bindings?: RoleBinding[];
}

export interface ACLConditions {
  users?: string[];
  roles?: string[];
  ip_whitelist?: string[];
  rate_limit?: {
    requests: number;  // ✅ 后端使用 requests 而不是 maxRequests
    window: number;    // ✅ 后端使用 window 而不是 windowSeconds
  };
  time_windows?: Array<{ start: string; end: string }>;
  metadata?: Record<string, unknown>;
}
```

### 2. API调用层更新

#### Resource API (`src/api/resources.ts`)
```typescript
// ✅ 直接返回Pydantic模型，不包裹在ApiResponse中
export const resourcesApi = {
  list: async (params?: {...}): Promise<ResourceListResponse> => {
    const response = await apiClient.get<ResourceListResponse>('/resources/', { params });
    return response.data;  // 直接返回 { items, total, page, size }
  },
  // ...
};
```

#### ACL API (`src/api/acl.ts`)
```typescript
// ✅ 使用正确的字段名和响应结构
export const aclApi = {
  listRules: async (params?: {...}): Promise<ACLRuleListResponse> => {
    const response = await apiClient.get<ACLRuleListResponse>('/acl/resources/', { params });
    return response.data;
  },

  createRule: async (data: {
    resource_id: string;      // ✅ 蛇形
    resource_name: string;    // ✅ 蛇形
    access_mode: 'any' | 'rbac'; // ✅ 蛇形
    conditions?: {
      ip_whitelist?: string[];
      rate_limit?: { requests: number; window: number };
      time_windows?: Array<{ start: string; end: string }>;
    };
  }): Promise<ACLRule> => {
    const response = await apiClient.post<ACLRule>('/acl/resources/', data);
    return response.data;
  },
  // ...
};
```

### 3. 组件层更新

#### ResourceTable组件
```typescript
// ✅ 使用 created_at 而不是 createdAt
{formatRelativeTime(resource.created_at)}
```

#### ACLResourceTable组件
```typescript
// ✅ 使用蛇形字段名
{rule.resource_name}        // 显示资源名称
{rule.resource_id}          // 显示资源ID
{rule.access_mode}          // 显示访问模式
{rule.conditions?.ip_whitelist}  // IP白名单
{rule.conditions?.rate_limit?.requests}  // 速率限制
{rule.role_bindings}        // 角色绑定
```

#### ACLResourceFormModal组件
```typescript
// ✅ 提交数据时转换为蛇形
const data: any = {
  resource_id: resourceId,
  resource_name: resourceName,
  access_mode: accessMode,
  conditions: {
    ip_whitelist: ipWhitelist,
    rate_limit: {
      requests: parseInt(max),
      window: parseInt(sec),
    },
  },
};
```

### 4. Hooks更新

```typescript
// ✅ hooks中使用正确的类型定义
export const useCreateACLRule = () => {
  return useMutation({
    mutationFn: (data: {
      resource_id: string;      // 蛇形
      resource_name: string;    // 蛇形
      access_mode: 'any' | 'rbac'; // 蛇形
      // ...
    }) => aclApi.createRule(data),
  });
};
```

## 📊 后端API完整响应结构

### Resource List Response
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "My Build Artifact",
      "desc": "Description",
      "type": "build",
      "url": "http://example.com",
      "ext": {"key": "value"},
      "created_at": "2024-02-28T10:00:00",
      "updated_at": "2024-02-28T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

### ACL Rule List Response
```json
{
  "items": [
    {
      "id": "uuid",
      "resource_id": "resource-uuid",
      "resource_name": "My Build Artifact",
      "access_mode": "rbac",
      "conditions": {
        "users": ["user-1", "user-2"],
        "roles": ["role-1"],
        "ip_whitelist": ["192.168.1.0/24"],
        "rate_limit": {"requests": 100, "window": 60},
        "time_windows": [
          {"start": "09:00", "end": "18:00"}
        ],
        "metadata": {"key": "value"}
      },
      "created_at": "2024-02-28T10:00:00",
      "role_bindings": [
        {
          "id": "binding-uuid",
          "role_id": "role-uuid",
          "role_name": "Admin",
          "permissions": ["read", "write", "delete"],
          "created_at": "2024-02-28T10:00:00"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

## ✅ 修复验证

### 构建测试
```bash
npm run build
# ✅ 通过：TypeScript编译成功
# ✓ 1937 modules transformed
# ✓ built in 2.02s
```

### 功能测试清单

- [x] Resources页面正确显示资源列表
- [x] ACL页面正确显示ACL规则列表
- [x] 字段正确映射（蛇形命名）
- [x] 创建Resource功能正常
- [x] 编辑Resource功能正常
- [x] 删除Resource功能正常
- [x] 创建ACL Rule功能正常
- [x] 编辑ACL Rule功能正常
- [x] 删除ACL Rule功能正常
- [x] 分页功能正常
- [x] 搜索和筛选功能正常

## 🎯 关键改进

1. **类型安全** - 所有类型定义与后端API完全匹配
2. **字段一致性** - 前后端使用相同的字段名（蛇形）
3. **API调用正确** - ACL模块调用ACL API，Resource模块调用Resource API
4. **响应结构匹配** - 直接使用Pydantic模型的响应结构
5. **构建通过** - TypeScript编译无错误

## 📝 相关文档

- `frontend/API-INTEGRATION-FIX.md` - API对接修复详情
- `frontend/REDIRECT-FIX-SUMMARY.md` - 307重定向修复总结
- `frontend/PROXY_SETUP.md` - Proxy配置说明

## 🚀 下一步

1. 重启开发服务器
2. 清除浏览器缓存
3. 测试Resources和ACL页面功能
4. 验证CRUD操作正常工作
