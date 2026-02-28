# 🔧 307重定向问题修复指南

## 🐛 问题原因

FastAPI在处理没有尾部斜杠的路径时（如 `/api/v1/resources`）会返回 **307 Temporary Redirect**，重定向到带斜杠的路径（`/api/v1/resources/`）。

**关键问题**: 重定向的 `location` 头包含完整的绝对URL `http://localhost:8000/api/v1/resources/`，导致浏览器直接访问8000端口，绕过了Vite proxy。

## ✅ 解决方案

在axios请求拦截器中自动为集合端点添加尾部斜杠，避免触发FastAPI的重定向。

### 修改的文件

1. **`src/api/client.ts`** - 添加了 `ensureTrailingSlash` 函数
2. **`vite.config.ts`** - 简化了proxy配置，添加了重定向警告日志

### 工作原理

```typescript
// 自动为集合端点添加尾部斜杠
const ensureTrailingSlash = (url: string): string => {
  // 跳过已有查询参数的URL
  if (url.includes('?')) return url;

  // 跳过已有尾部斜杠的URL
  if (url.endsWith('/')) return url;

  // 为集合端点添加斜杠
  const collectionPatterns = [
    /\/resources$/,
    /\/acl\/resources$/,
    // ... 更多模式
  ];

  for (const pattern of collectionPatterns) {
    if (pattern.test(url)) {
      return url + '/';
    }
  }

  return url;
};
```

## 🧪 验证修复

### 1. 重启Vite开发服务器

```bash
# 停止当前服务器 (Ctrl+C)
npm run dev
```

### 2. 清除浏览器缓存

```javascript
// 在浏览器Console中执行
localStorage.clear()
location.reload()
```

### 3. 检查请求日志

在浏览器Console中应该看到：

```
🔄 Auto-adding trailing slash: /resources -> /resources/
🚀 API Request: {
  method: "GET",
  url: "/resources/",
  fullURL: "/api/v1/resources/",
  hasToken: true
}
```

在Vite终端中应该看到：

```
🔄 Proxy: GET /api/v1/resources/ -> /api/v1/resources/
```

### 4. 验证Network面板

打开浏览器开发者工具 → Network标签：

- ✅ **正确**: `Request URL: http://localhost:5173/api/v1/resources/?page=1&pageSize=20`
- ✅ **Status**: `200 OK` (不是307)
- ✅ **Remote Address**: `localhost:5173`

## 📋 覆盖的端点

以下端点会自动添加尾部斜杠：

- `/resources` → `/resources/`
- `/acl/resources` → `/acl/resources/`
- `/acl/rules` → `/acl/rules/`
- `/users` → `/users/`
- `/roles` → `/roles/`
- `/permissions` → `/permissions/`
- `/gateways` → `/gateways/`

## 🚫 不受影响的请求

以下请求不会添加斜杠：

- 带查询参数: `/resources?page=1`
- 带ID的请求: `/resources/123`
- 已有斜杠: `/resources/`
- 非集合端点

## 🐛 如果问题仍然存在

1. **检查Vite日志** - 确认没有看到307重定向警告
2. **检查Console日志** - 确认URL已添加斜杠
3. **手动测试** - 在Console中测试:
   ```javascript
   fetch('/api/v1/resources/')
     .then(r => r.json())
     .then(console.log)
   ```
4. **检查后端** - 确认FastAPI路由配置

## 🔍 调试命令

```bash
# 测试后端是否返回307
curl -I http://localhost:8000/api/v1/resources

# 应该看到:
# HTTP/1.1 307 Temporary Redirect
# location: http://localhost:8000/api/v1/resources/

# 测试带斜杠的URL（应该返回401或200，取决于认证）
curl -I http://localhost:8000/api/v1/resources/
