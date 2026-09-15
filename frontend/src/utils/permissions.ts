import { Resource, User } from '@/types';

/** True when the user holds the `admin` or `super_admin` role. */
export const isAdminUser = (user?: User | null): boolean =>
  user?.roles?.some((role) => role.name === 'admin' || role.name === 'super_admin') ?? false;

/**
 * True when the user may edit or delete `resource`.
 *
 * Mirrors the backend's `_check_write_permission`: the owner plus
 * admin/super_admin, and an ownerless resource is admin-only. The backend is
 * the authority - this only decides whether to offer the action, so that
 * users are not shown buttons that will come back 403.
 */
export const canManageResource = (resource: Resource, user?: User | null): boolean => {
  if (isAdminUser(user)) return true;
  if (!user || !resource.owner_id) return false;
  return resource.owner_id === user.id;
};
