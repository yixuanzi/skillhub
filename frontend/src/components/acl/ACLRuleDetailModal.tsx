import { Lock, Unlock } from 'lucide-react';
import { Modal, Badge, Alert } from '@/components/ui';
import { ACLRule } from '@/types';

interface ACLRuleDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  rule?: ACLRule | null;
}

const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="space-y-1">
    <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
    <div className="text-sm text-gray-200 break-words">{children}</div>
  </div>
);

const Empty = () => <span className="text-gray-600 font-mono">—</span>;

/**
 * Read-only view of an ACL rule, for users who may see it but not manage it.
 *
 * ACL rules are managed by the resource's owner and by admins; everyone else
 * who has been granted access can see the rule that grants it, which is worth
 * being able to read.
 */
export const ACLRuleDetailModal = ({ isOpen, onClose, rule }: ACLRuleDetailModalProps) => {
  if (!rule) return null;

  const conditions = rule.conditions as Record<string, unknown> | undefined;
  const hasConditions = !!conditions && Object.keys(conditions).length > 0;
  const bindings = rule.role_bindings ?? [];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`ACL rule: ${rule.resource_name}`} size="lg">
      <div className="space-y-5">
        <Alert variant="info">
          Read-only view. Only the resource owner and administrators can edit or delete this rule.
        </Alert>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Resource">
            <code className="font-mono text-cyber-primary">{rule.resource_name}</code>
          </Field>
          <Field label="Access mode">
            {rule.access_mode === 'any' ? (
              <Badge variant="success" className="gap-1.5 font-mono uppercase">
                <Unlock className="w-3 h-3" /> any
              </Badge>
            ) : (
              <Badge variant="warning" className="gap-1.5 font-mono uppercase">
                <Lock className="w-3 h-3" /> rbac
              </Badge>
            )}
          </Field>
          <Field label="Resource ID">
            <code className="font-mono text-xs text-gray-500">{rule.resource_id}</code>
          </Field>
          <Field label="Rule ID">
            <code className="font-mono text-xs text-gray-500">{rule.id}</code>
          </Field>
        </div>

        <Field label="Conditions">
          {hasConditions ? (
            <pre className="max-h-64 overflow-auto rounded border border-void-700 bg-void-900 p-3 text-xs font-mono text-gray-300">
              {JSON.stringify(conditions, null, 2)}
            </pre>
          ) : (
            <Empty />
          )}
        </Field>

        <Field label={`Role bindings (${bindings.length})`}>
          {bindings.length > 0 ? (
            <ul className="space-y-1.5">
              {bindings.map((binding) => (
                <li key={binding.id} className="flex items-center gap-2 text-xs">
                  <code className="font-mono text-cyber-secondary">
                    {binding.role_name || binding.role_id}
                  </code>
                  <span className="text-gray-500 font-mono">
                    {(binding.permissions ?? []).join(', ') || '—'}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <Empty />
          )}
        </Field>
      </div>
    </Modal>
  );
};
