# ✅ ACL和Resource API对接修复完成

## 🐛 发现的问题

1. **ACL模块调用了错误的API** - ACL page调用了resource API而不是ACL API
2. **字段命名不匹配** - 后端使用蛇形命名（snake_case），前端期望驼峰命名（camelCase）
3. **API响应结构不匹配** - 后端直接返回Pydantic模型，前端期望包裹在ApiResponse中

## 🛠️ 修复内容

### 1. **类型定义更新** (`src/types/index.ts`)

#### Resource类型 - 使用蛇形命名
```typescript
export interface Resource {
  id: string;
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  created_at: string;      // ✅ 改为蛇形
  updated_at: string;      // ✅ 改为蛇形
}
```

#### ACL类型 - 使用蛇形命名
```typescript
export interface ACLRule {
  id: string;
  resource_id: string;        // ✅ 蛇形
  resource_name: string;      // ✅ 蛇形
  access_mode: AccessMode;    // ✅ 蛇形
  conditions?: ACLConditions;
  created_at: string;         // ✅ 蛇形
  role_bindings?: RoleBinding[];
}

export interface ACLConditions {
  users?: string[];
  roles?: string[];
  ip_whitelist?: string[];           // ✅ 蛇形
  rate_limit?: {
    requests: number;                // ✅ 后端字段名
    window: number;                  // ✅ 后端字段名
  };
  time_windows?: Array<{
    start: string;
    end: string;
  }>;
  metadata?: Record<string, unknown>;
}
```

### 2. **API调用更新**

#### `src/api/resources.ts` - 直接返回Pydantic模型
```typescript
export const resourcesApi = {
  list: async (params?: {...}): Promise<ResourceListResponse> => {
    const response = await apiClient.get<ResourceListResponse>('/resources/', { params });
    return response.data;  // ✅ 直接返回数据，不包裹在ApiResponse中
  },
  // ...
};
```

#### `src/api/acl.ts` - 使用正确的字段名
```typescript
export const aclApi = {
  listRules: async (params?: {...}): Promise<ACLRuleListResponse> => {
    const response = await apiClient.get<ACLRuleListResponse>('/acl/resources/', { params });
    return response.data;
  },

  createRule: async (data: {
    resource_id: string;        // ✅ 蛇形
    resource_name: string;      // ✅ 蛇形
    access_mode: 'any' | 'rbac'; // ✅ 蛇形
    role_bindings?: {...};
    conditions?: {
      ip_whitelist?: string[];   // ✅ 蛇形
      rate_limit?: {
        requests: number;        // ✅ 后端字段
        window: number;          // ✅ 后端字段
      };
      time_windows?: Array<{
        start: string;
        end: string;
      }>;
    };
  }): Promise<ACLRule> => {
    const response = await apiClient.post<ACLRule>('/acl/resources/', data);
    return response.data;
  },
  // ...
};
```

### 3. **组件更新** - 使用正确的字段名

#### `ResourceTable.tsx`
```typescript
{formatRelativeTime(resource.created_at)}  // ✅ 使用 created_at
```

#### `ACLResourceTable.tsx`
```typescript
{rule.resource_name}       // ✅ 使用 resource_name
{rule.resource_id}         // ✅ 使用 resource_id
{rule.access_mode}         // ✅ 使用 access_mode
{rule.conditions?.rate_limit?.requests}  // ✅ 使用后端字段
{rule.conditions?.ip_whitelist}          // ✅ 蛇形
{rule.role_bindings}       // ✅ 使用 role_bindings
```

#### `ACLResourceFormModal.tsx`
```typescript
// 表单提交时转换为蛇形
const data: any = {
  resource_id: resourceId,       // ✅ 蛇形
  resource_name: resourceName,   // ✅ 蛇形
  access_mode: accessMode,       // ✅ 蛇形
  conditions: {
    ip_whitelist: ipWhitelist,   // ✅ 蛇形
    rate_limit: {
      requests: parseInt(max),  // ✅ 后端字段
      window: parseInt(sec),    // ✅ 后端字段
    },
  },
};
```

### 4. **Hooks更新** (`src/hooks/useACL.ts`)
```typescript
export const useCreateACLRule = () => {
  return useMutation({
    mutationFn: (data: {
      resource_id: string;        // ✅ 蛇形
      resource_name: string;      // ✅ 蛇形
      access_mode: 'any' | 'rbac'; // ✅ 蛇形
      // ...
    }) => aclApi.createRule(data),
  });
};
```

## 📊 后端API返回结构

### Resource API
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "resource-name",
      "desc": "description",
      "type": "build",
      "url": "http://...",
      "ext": {},
      "created_at": "2024-02-28T10:00:00",
      "updated_at": "2024-02-28T10:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20
}
```

### ACL API
```json
{
  "items": [
    {
      "id": "uuid",
      "resource_id": "resource-uuid",
      "resource_name": "Resource Name",
      "access_mode": "rbac",
      "conditions": {
        "users": ["user-1"],
        "roles": ["role-1"],
        "ip_whitelist": ["192.168.1.1"],
        "rate_limit": {"requests": 100, "window": 60},
        "time_windows": [{"start": "09:00", "end": "18:00"}]
      },
      "created_at": "2024-02-28T10:00:00",
      "role_bindings": [
        {
          "id": "binding-uuid",
          "role_id": "role-uuid",
          "role_name": "Admin",
          "permissions": ["read", "write"],
          "created_at": "2024-02-28T10:00:00"
        }
      ]
    }
  ],
  "total": 5,
  "page": 1,
  "size": 20
}
```

## ✅ 修复后的效果

1. **ACL页面正确调用ACL API** (`/api/v1/acl/resources/`)
2. **Resource页面正确调用Resource API** (`/api/v1/resources/`)
3. **所有字段使用蛇形命名匹配后端**
4. **数据正确显示在列表中**
5. **表单正确提交和编辑数据**

## 🧪 验证步骤

1. 重启开发服务器
2. 清除浏览器缓存 (`localStorage.clear()`)
3. 访问 Resources 页面 - 应该看到资源列表
4. 访问 ACL 页面 - 应该看到ACL规则列表
5. 创建新的资源或ACL规则 - 应该成功提交
6. 编辑现有条目 - 应该正确加载和保存
