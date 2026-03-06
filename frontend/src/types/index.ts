// User & Auth Types
export interface User {
  id: string;
  username: string;
  email: string;
  roles: Role[];
  createdAt: string;
  updatedAt: string;
}

export interface Role {
  id: string;
  name: string;
  permissions: Permission[];
  createdAt: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  conditions?: Record<string, unknown>;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Skill Types
export type SkillRuntime = 'python' | 'nodejs' | 'go';
export type SkillType = 'business_logic' | 'api_proxy' | 'ai_llm' | 'data_processing';
export type SkillStatus = 'draft' | 'published' | 'archived';

export interface Skill {
  id: string;
  name: string;
  description: string;
  content?: string;
  created_by: string;
  category?: string;
  tags?: string;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface SkillVersion {
  id: string;
  skill_id: string;
  version: string;
  status: 'draft' | 'published';
  artifact_path: string;
  checksum: string;
  created_by: string;
  created_at: string;
  changelog?: string;
}

export interface SkillCreateRequest {
  name: string;
  description: string;
  content?: string;
  category?: string;
  tags?: string;
  version?: string;
}

export interface SkillUpdateRequest {
  name?: string;
  description?: string;
  content?: string;
  category?: string;
  tags?: string;
  version?: string;
}

export interface SkillInvokeRequest {
  skill_id: string;
  version?: string;
  params: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface SkillInvokeResponse {
  success: boolean;
  data?: unknown;
  error?: {
    code: string;
    message: string;
  };
  metadata: {
    executionTime: number;
    version: string;
    cached: boolean;
  };
  requestId: string;
}

// Resource Types
export type ResourceType = 'gateway' | 'third' | 'mcp';
export type ViewScope = 'public' | 'private';
export type MCPTransportType = 'stdio' | 'sse' | 'ws' | 'httpstream';

export interface MCPConfig {
  transport: MCPTransportType;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  timeout?: number;
  endpoint?: string;
}

export interface Resource {
  id: string;
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  view_scope: ViewScope;
  api_description?: string;
  owner_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ResourceCreate {
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  view_scope?: ViewScope;
  api_description?: string;
}

export interface ResourceUpdate {
  name?: string;
  desc?: string;
  type?: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  view_scope?: ViewScope;
  api_description?: string;
}

// ACL Types
export type AccessMode = 'any' | 'rbac';

export interface ACLRule {
  id: string;
  resource_id: string;
  resource_name: string;
  access_mode: AccessMode;
  conditions?: ACLConditions;
  created_at: string;
  role_bindings?: RoleBinding[];
}

export interface RoleBinding {
  id: string;
  role_id: string;
  role_name?: string;
  permissions: string[];
  created_at: string;
}

export interface ACLConditions {
  users?: string[];
  roles?: string[];
  ip_whitelist?: string[];
  rate_limit?: {
    requests: number;
    window: number;
  };
  time_windows?: Array<{
    start: string;
    end: string;
  }>;
  metadata?: Record<string, unknown>;
}

export interface AuditLog {
  id: string;
  resourceId: string;
  userId: string;
  accessGranted: boolean;
  ipAddress: string;
  timestamp: string;
  details: Record<string, unknown>;
}

// MToken Types
export interface MToken {
  id: string;
  app_name: string;
  key_name: string;
  value: string;
  desc?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface MTokenCreate {
  app_name: string;
  key_name: string;
  value: string;
  desc?: string;
}

export interface MTokenUpdate {
  app_name?: string;
  key_name?: string;
  value?: string;
  desc?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// API Response Wrapper (for other APIs that still use it)
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown[];
  };
}
