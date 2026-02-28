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
  type: SkillType;
  runtime: SkillRuntime;
  status: SkillStatus;
  currentVersion: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, unknown>;
}

export interface SkillVersion {
  id: string;
  skillId: string;
  version: string;
  status: 'draft' | 'published';
  artifactPath: string;
  checksum: string;
  createdBy: string;
  createdAt: string;
  changelog?: string;
}

export interface SkillCreateRequest {
  name: string;
  description: string;
  type: SkillType;
  runtime: SkillRuntime;
  code: string;
  requirements?: string;
  metadata?: Record<string, unknown>;
}

export interface SkillInvokeRequest {
  skillId: string;
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

// ACL Types
export type AccessMode = 'any' | 'rbac';

export interface ACLRule {
  id: string;
  resourceId: string;
  accessMode: AccessMode;
  roles?: string[];
  conditions: ACLConditions;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ACLConditions {
  rateLimit?: {
    maxRequests: number;
    windowSeconds: number;
  };
  ipWhitelist?: string[];
  timeWindows?: Array<{
    start: string;
    end: string;
    days: number[];
  }>;
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

// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown[];
  };
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
