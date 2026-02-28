# SkillHub 设计文档总览

## 📋 文档导航

本目录包含 SkillHub 平台的完整设计文档，涵盖架构、模块、API、数据模型和技术选型。

### 核心设计文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [PRD.md](./PRD.md) | **产品需求文档** | ✅ 完成 |
| [../design.md](../design.md) | **插件项目功能模块设计** | ✅ 完成 |
| [architecture.md](./architecture.md) | 系统架构设计 | ✅ 完成 |
| [modules.md](./modules.md) | 核心模块设计 | ✅ 完成 |
| [api-design.md](./api-design.md) | API 接口设计 | ✅ 完成 |
| [data-model.md](./data-model.md) | 数据模型设计 | ✅ 完成 |
| [tech-stack.md](./tech-stack.md) | 技术栈选型 | ✅ 完成 |
| [security.md](./security.md) | 安全设计 | ✅ 完成 |
| [deployment.md](./deployment.md) | 部署指南 | ✅ 完成 |
| [development.md](./development.md) | 开发指南 | ✅ 完成 |

---

## 🎯 项目概述

### 产品定位

SkillHub 是一个**企业级内部技能生态系统平台**，旨在统一管理、发布和调用内部技能（Skills）。

### 核心功能

#### 1. Internal Skill Build & Publish（内部技能构建与发布）

**构建（Build）**：
- 提供工具和环境，快速封装业务逻辑、算法或特定功能
- 支持代码编写、配置管理、依赖项打包
- 多运行时支持：Node.js, Python, Go

**发布（Publish）**：
- 标准化流程部署到运行时环境
- 版本控制、元数据管理
- 灰度发布、蓝绿部署、一键回滚

#### 2. Gateway Call（网关调用）

- **统一入口**：所有内部技能调用必须通过网关
- **统一 API**：标准化接口，支持 Dify/n8n 快速构建
- **请求路由**：负载均衡，高可用性
- **资源支持**：
  - 内部托管 API
  - 内部独立 API
  - 第三方 API URL
- **Token 管理**：校验后获取托管应用令牌

#### 3. Call ACL（调用访问控制列表）

- **访问模式**：
  - `any`：任意访问
  - `rbac`：基于角色的访问控制
- **条件控制**：限流、IP 白名单、时间窗口等
- **审计日志**：完整的访问记录

#### 4. 用户认证与 RBAC 权限

- **用户登录**：认证并返回 JWT Token
- **RBAC 模型**：用户-角色-权限-资源
- **精细化权限**：多资源的细粒度权限设置

---

## 🏗️ 系统架构

### 架构层次

```
┌─────────────────────────────────────────┐
│         客户端层 (Client Layer)          │
│   Web UI  │  Admin UI  │  SDK/CLI      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         网关层 (Gateway Layer)           │
│   API Gateway  │  Auth  │  ACL          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       核心服务层 (Service Layer)         │
│  Build  │  Publish  │  Registry  │ Dify │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       数据层 (Data Layer)                │
│  PostgreSQL  │  Redis  │  MinIO/S3      │
└─────────────────────────────────────────┘
```

### 核心组件

1. **API Gateway**：统一入口，路由分发，限流
2. **Auth Service**：用户认证，JWT Token 管理
3. **ACL Service**：访问控制，权限校验
4. **Skill Build Service**：技能构建和测试
5. **Skill Publish Service**：技能发布和部署
6. **Skill Registry**：技能注册和发现
7. **Dify Gateway**：API 编排和 LLM 集成

---

## 📊 数据流

### 技能调用流程

```
用户 → API Gateway → Auth(验证Token) → ACL(检查权限)
  → Skill Registry(查询技能) → Dify Gateway → 技能实例
  → 返回结果
```

### 技能发布流程

```
开发者 → 上传代码 → Build Service(构建)
  → Test(测试) → Publish Service(发布)
  → Registry(注册) → Gateway(配置路由)
  → 完成
```

---

## 🔐 安全设计

### 认证机制

- **JWT Token**：15 分钟有效期，可刷新
- **Refresh Token**：7 天有效期
- **密码存储**：bcrypt 哈希

### 访问控制

- **RBAC 模型**：用户-角色-权限-资源
- **ACL 规则**：支持 any 和 rbac 两种模式
- **条件约束**：限流、IP 白名单、时间窗口

### 数据安全

- **传输加密**：TLS 1.3
- **存储加密**：敏感数据加密存储
- **审计日志**：完整的操作记录

---

## 🚀 技术栈

### 前端

- React 18 + TypeScript
- Vite + Tailwind CSS
- React Query + Zustand

### 后端

- **认证服务**：Node.js + Express + Passport.js
- **核心服务**：Go + Gin + GORM + Casbin

### 数据存储

- **PostgreSQL 15+**：主数据库
- **Redis 7.x**：缓存和 Session
- **MinIO/S3**：对象存储

### 基础设施

- **Kubernetes**：容器编排
- **Kong Gateway**：API 网关
- **Dify**：快速构建平台
- **Prometheus + Grafana**：监控
- **ELK Stack**：日志

---

## 📈 非功能性需求

### 性能指标

- API 响应时间：P99 < 200ms
- 技能调用吞吐量：> 10,000 QPS
- 系统可用性：99.9%

### 可扩展性

- 水平扩展：无状态服务设计
- 数据库：读写分离，分区表
- 缓存策略：多级缓存

### 可观测性

- **监控**：Prometheus + Grafana
- **日志**：Fluent Bit + ELK
- **追踪**：OpenTelemetry + Jaeger

---

## 🗓️ 开发计划

### Phase 1: 基础设施（2 周）

- [ ] 数据库 schema 设计和实现
- [ ] 基础服务框架搭建
- [ ] CI/CD 流水线配置
- [ ] 开发环境搭建

### Phase 2: 认证与权限（2 周）

- [ ] 用户认证服务
- [ ] JWT Token 管理
- [ ] RBAC 权限系统
- [ ] ACL 规则引擎

### Phase 3: 技能管理（3 周）

- [ ] 技能构建服务
- [ ] 技能发布流程
- [ ] 技能注册中心
- [ ] 版本管理

### Phase 4: 网关集成（2 周）

- [ ] API Gateway 配置
- [ ] Dify 平台集成
- [ ] 技能调用接口
- [ ] 负载均衡

### Phase 5: 前端开发（3 周）

- [ ] Web 管理界面
- [ ] 管理后台
- [ ] 技能市场 UI
- [ ] 监控仪表板

### Phase 6: 测试与优化（2 周）

- [ ] 单元测试和集成测试
- [ ] 性能测试和优化
- [ ] 安全测试
- [ ] 文档完善

---

## 📚 参考资源

### 外部文档

- [Dify 官方文档](https://docs.dify.ai/)
- [Kong Gateway 文档](https://docs.konghq.com/)
- [Casbin 权限框架](https://casbin.org/)
- [OpenTelemetry 规范](https://opentelemetry.io/)

### 相关项目

- ClawHub：公开技能市场
- OpenClaw：AI Agent 框架

---

## 👥 团队和联系

- **项目负责人**：[待定]
- **架构师**：[待定]
- **开发团队**：[待定]
- **文档维护**：AI Assistant (小黑 🐕)

---

## 📝 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2024-02-27 | v1.0 | 初始设计文档 |

---

*本文档由 AI Assistant (小黑 🐕) 协助创建和维护*
