import { Globe, Lock } from 'lucide-react';
import { Modal, Badge, Alert } from '@/components/ui';
import { Resource } from '@/types';

interface ResourceDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  resource?: Resource | null;
}

const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="space-y-1">
    <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
    <div className="text-sm text-gray-200 break-words">{children}</div>
  </div>
);

const Empty = () => <span className="text-gray-600 font-mono">—</span>;

/**
 * Read-only view of a resource, for users who may see it but not manage it.
 *
 * The `ext` shown here is whatever the API returned: the backend masks secret
 * values for anyone who is not the owner or an admin, so this may legitimately
 * show "***". That is surfaced explicitly rather than silently, so nobody
 * mistakes a masked value for the configured one.
 */
export const ResourceDetailModal = ({ isOpen, onClose, resource }: ResourceDetailModalProps) => {
  if (!resource) return null;

  const ext = resource.ext as Record<string, unknown> | undefined;
  const hasExt = !!ext && Object.keys(ext).length > 0;
  const isRedacted = hasExt && JSON.stringify(ext).includes('"***"');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Resource: ${resource.name}`} size="lg">
      <div className="space-y-5">
        <Alert variant="info">
          Read-only view. Only the resource owner and administrators can edit or delete it.
        </Alert>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Name">
            <code className="font-mono text-cyber-primary">{resource.name}</code>
          </Field>
          <Field label="Type">
            <Badge variant="info">{resource.type}</Badge>
          </Field>
          <Field label="ID">
            <code className="font-mono text-xs text-gray-500">{resource.id}</code>
          </Field>
          <Field label="Visibility">
            {resource.view_scope === 'public' ? (
              <span className="inline-flex items-center gap-1.5 text-cyber-primary">
                <Globe className="w-3.5 h-3.5" /> public
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-gray-400">
                <Lock className="w-3.5 h-3.5" /> private
              </span>
            )}
          </Field>
        </div>

        <Field label="URL">
          {resource.url ? (
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs text-cyber-secondary hover:text-cyber-primary transition-colors"
            >
              {resource.url}
            </a>
          ) : (
            <Empty />
          )}
        </Field>

        <Field label="Description">{resource.desc || <Empty />}</Field>

        <Field label="Configuration (ext)">
          {hasExt ? (
            <>
              {isRedacted && (
                <p className="mb-2 text-xs text-gray-500">
                  Values shown as <code className="font-mono">***</code> are hidden because you are
                  not the owner of this resource. Placeholders like{' '}
                  <code className="font-mono">{'{token_name}'}</code> are shown as configured.
                </p>
              )}
              <pre className="max-h-64 overflow-auto rounded border border-void-700 bg-void-900 p-3 text-xs font-mono text-gray-300">
                {JSON.stringify(ext, null, 2)}
              </pre>
            </>
          ) : (
            <Empty />
          )}
        </Field>

        {resource.api_description && (
          <Field label="API documentation">
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded border border-void-700 bg-void-900 p-3 text-xs text-gray-300">
              {resource.api_description}
            </pre>
          </Field>
        )}
      </div>
    </Modal>
  );
};
