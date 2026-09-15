import { ACLRule, Resource, User } from '@/types';

/** True when the user holds the `admin` or `super_admin` role. */
export const isAdminUser = (user?: User | null): boolean =>
  user?.roles?.some((role) => role.name === 'admin' || role.name === 'super_admin') ?? false;

/**
 * True when the user may edit or delete `resource`.
 *
 * The verdict comes from the server, which sets `can_manage` on every resource
 * it returns, so the rule (owner plus admin; an ownerless resource is
 * admin-only) lives in exactly one place and cannot drift out of sync here.
 * This only decides whether to offer the action - the server still enforces it
 * on the write itself.
 */
export const canManageResource = (resource: Resource): boolean => resource.can_manage === true;

/**
 * True when the user may edit or delete `rule`.
 *
 * Same contract as {@link canManageResource}: the verdict is the server's
 * (`can_manage`), which for an ACL rule means the owner of the rule's resource
 * plus admin/super_admin.
 */
export const canManageAclRule = (rule: ACLRule): boolean => rule.can_manage === true;
