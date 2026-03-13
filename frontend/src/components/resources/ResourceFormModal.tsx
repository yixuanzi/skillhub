import React, { useState, useEffect } from 'react';
import { Lock, Globe, Server } from 'lucide-react';
import {
  Modal,
  Input,
  Textarea,
  Alert,
  Button,
  Label,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui';
import { JsonEditor } from './JsonEditor';
import { Resource, ResourceCreate, ResourceType, MCPConfig, MCPTransportType, ViewScope } from '@/types';

interface ResourceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ResourceCreate) => Promise<void>;
  resource?: Resource;
  mode: 'create' | 'edit';
}

// Helper to parse MCP config from ext
const parseMcpConfig = (ext?: Record<string, unknown>): MCPConfig | undefined => {
  if (!ext) return undefined;

  const mcpConfig = ext.mcp_config as MCPConfig | undefined;
  if (!mcpConfig) return undefined;

  return mcpConfig;
};

export const ResourceFormModal: React.FC<ResourceFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  resource,
  mode,
}) => {
  // Form state
  const [name, setName] = useState('');
  const [type, setType] = useState<ResourceType>('gateway');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [viewScope, setViewScope] = useState<ViewScope>('public');
  const [apiDescription, setApiDescription] = useState('');
  const [httpMethod, setHttpMethod] = useState<'GET' | 'POST' | 'PUT' | 'DELETE'>('GET');

  // MCP config state
  const [mcpTransport, setMcpTransport] = useState<MCPTransportType>('stdio');
  const [mcpCommand, setMcpCommand] = useState('');
  const [mcpArgs, setMcpArgs] = useState('');
  const [mcpEndpoint, setMcpEndpoint] = useState('');
  const [mcpTimeout, setMcpTimeout] = useState('30000');
  const [mcpHeaders, setMcpHeaders] = useState('');

  // UI state
  const [ext, setExt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && resource) {
        setName(resource.name);
        setType(resource.type);
        setUrl(resource.url || '');
        setDescription(resource.desc || '');
        setViewScope(resource.view_scope || 'public');
        setApiDescription(resource.api_description || '');

        // Parse HTTP method from ext for third type
        const methodFromExt = resource.ext?.method as string | undefined;
        if (methodFromExt && ['GET', 'POST', 'PUT', 'DELETE'].includes(methodFromExt)) {
          setHttpMethod(methodFromExt as 'GET' | 'POST' | 'PUT' | 'DELETE');
        } else {
          setHttpMethod('GET');
        }

        // Parse MCP config from ext
        const mcpConfig = parseMcpConfig(resource.ext);
        if (mcpConfig) {
          // Use 'sse' as default if transport is 'stdio' or 'ws' (not supported)
          const transport = mcpConfig.transport || 'sse';
          const supportedTransport = (transport === 'stdio' || transport === 'ws') ? 'sse' : transport;
          setMcpTransport(supportedTransport as MCPTransportType);
          setMcpCommand(mcpConfig.command || '');
          setMcpArgs(mcpConfig.args ? mcpConfig.args.join(' ') : '');
          setMcpEndpoint(mcpConfig.endpoint || '');
          setMcpTimeout(String(mcpConfig.timeout || 30000));
          setMcpHeaders(mcpConfig.headers ? JSON.stringify(mcpConfig.headers, null, 2) : '');
        }

        setExt(resource.ext ? JSON.stringify(resource.ext, null, 2) : '');
      } else {
        setName('');
        setType('gateway');
        setUrl('');
        setDescription('');
        setViewScope('public');
        setApiDescription('');
        setHttpMethod('GET');
        setMcpTransport('sse'); // Default to SSE (supported) instead of stdio
        setMcpCommand('');
        setMcpArgs('');
        setMcpEndpoint('');
        setMcpTimeout('30000');
        setMcpHeaders('');
        setExt('');
      }
      setError('');
    }
  }, [isOpen, mode, resource]);

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setError('Name is required');
      return false;
    }

    // Validate URL for gateway and third types
    if ((type === 'gateway' || type === 'third') && !url.trim()) {
      setError('URL is required for Gateway and Third Party types');
      return false;
    }

    // Validate MCP config
    if (type === 'mcp') {
      if (mcpTransport === 'stdio' && !mcpCommand.trim()) {
        setError('Command is required for STDIO transport');
        return false;
      }
      if ((mcpTransport === 'sse' || mcpTransport === 'ws' || mcpTransport === 'httpstream') && !mcpEndpoint.trim()) {
        setError('Endpoint is required for SSE, WebSocket, and HTTP Stream transports');
        return false;
      }

      // Validate headers JSON if provided
      if (mcpHeaders.trim()) {
        try {
          JSON.parse(mcpHeaders);
        } catch {
          setError('Invalid JSON in header variables');
          return false;
        }
      }
    }

    // Validate JSON in ext field if provided
    if (ext.trim()) {
      try {
        JSON.parse(ext);
      } catch {
        setError('Invalid JSON in extended properties');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Build ext object
      let extObj: Record<string, unknown> | undefined;

      // Parse existing ext or create new
      if (ext.trim()) {
        try {
          extObj = JSON.parse(ext);
        } catch {
          extObj = {};
        }
      }

      // Add HTTP method to ext for third type
      if (type === 'third') {
        extObj = extObj || {};
        extObj.method = httpMethod;
      }

      // Add MCP config to ext
      if (type === 'mcp') {
        const mcpConfig: MCPConfig = {
          transport: mcpTransport,
          timeout: parseInt(mcpTimeout) || 30000,
        };

        if (mcpTransport === 'stdio') {
          mcpConfig.command = mcpCommand;
          if (mcpArgs.trim()) {
            mcpConfig.args = mcpArgs.split(' ').filter(Boolean);
          }
        } else {
          mcpConfig.endpoint = mcpEndpoint;
        }

        if (mcpHeaders.trim()) {
          try {
            mcpConfig.headers = JSON.parse(mcpHeaders) as Record<string, string>;
          } catch {
            // Skip if invalid
          }
        }

        extObj = extObj || {};
        extObj.mcp_config = mcpConfig;
      }

      const data: ResourceCreate = {
        name: name.trim(),
        type,
        url: url.trim() || undefined,
        desc: description.trim() || undefined,
        view_scope: viewScope,
        api_description: apiDescription.trim() || undefined,
        ext: Object.keys(extObj || {}).length > 0 ? extObj : undefined,
      };

      await onSubmit(data);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save resource';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const resourceTypes: { value: ResourceType; label: string; icon?: React.ReactNode }[] = [
    { value: 'gateway', label: 'Gateway Resource' },
    { value: 'third', label: 'Third-party API' },
    { value: 'mcp', label: 'MCP Server', icon: <Server className="w-4 h-4" /> },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Create Resource' : 'Edit Resource'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Error Alert */}
        {error && (
          <Alert variant="danger">
            <span className="text-sm font-medium">{error}</span>
          </Alert>
        )}

        {/* Name Field */}
        <Input
          label="Name *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-resource"
          required
        />

        {/* Type Field */}
        <div className="flex flex-col gap-1.5">
          <Label>Type *</Label>
          <Select value={type} onValueChange={(v) => setType(v as ResourceType)}>
            <SelectTrigger>
              <SelectValue placeholder="Select resource type" />
            </SelectTrigger>
            <SelectContent>
              {resourceTypes.map(({ value, label, icon }) => (
                <SelectItem key={value} value={value}>
                  <div className="flex items-center gap-2">
                    {icon}
                    <span>{label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* URL Field (for gateway/third) */}
        {(type === 'gateway' || type === 'third') && (
          <Input
            label="URL *"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://api.example.com"
            type="url"
            required
          />
        )}

        {/* HTTP Method Field (for third type only) */}
        {type === 'third' && (
          <div className="flex flex-col gap-1.5">
            <Label>HTTP Method *</Label>
            <Select value={httpMethod} onValueChange={(v) => setHttpMethod(v as 'GET' | 'POST' | 'PUT' | 'DELETE')}>
              <SelectTrigger>
                <SelectValue placeholder="Select HTTP method" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GET">GET</SelectItem>
                <SelectItem value="POST">POST</SelectItem>
                <SelectItem value="PUT">PUT</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Description Field */}
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Resource description"
          rows={2}
        />

        {/* View Scope Selection */}
        <div className="flex flex-col gap-1.5">
          <Label>Visibility *</Label>
          <Select value={viewScope} onValueChange={(v) => setViewScope(v as ViewScope)}>
            <SelectTrigger>
              <SelectValue placeholder="Select visibility" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="public">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  <span>Public - Visible to all users</span>
                </div>
              </SelectItem>
              <SelectItem value="private">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  <span>Private - Only you and ACL-allowed users</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* API Description (for gateway/third) */}
        {(type === 'gateway' || type === 'third') && (
          <Textarea
            label="API Documentation (Markdown)"
            value={apiDescription}
            onChange={(e) => setApiDescription(e.target.value)}
            placeholder={`# API Description

Describe what this API does and its use case.

## Example Usage

\`\`\`bash
curl -X POST https://api.example.com/endpoint \\
  -H "Authorization: Bearer {token}" \\
  -d '{"param": "value"}'
\`\`\`

## Parameters
- \`param\`: Description of parameter

## Response Format
\`\`\`json
{"result": "success"}
\`\`\``}
            rows={10}
            className="font-mono text-sm"
          />
        )}

        {/* MCP Configuration (for mcp type) */}
        {type === 'mcp' && (
          <div className="space-y-4 border border-void-700 rounded-lg p-4">
            <h3 className="font-semibold text-gray-100">MCP Server Configuration</h3>

            {/* Transport Type */}
            <div className="flex flex-col gap-1.5">
              <Label>Transport Type *</Label>
              <Select value={mcpTransport} onValueChange={(v) => setMcpTransport(v as MCPTransportType)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select transport type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stdio" disabled>STDIO (Command) - Not Supported</SelectItem>
                  <SelectItem value="sse">Server-Sent Events</SelectItem>
                  <SelectItem value="ws" disabled>WebSocket - Not Supported</SelectItem>
                  <SelectItem value="httpstream">HTTP Stream</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                Note: STDIO and WebSocket transports are currently not supported
              </p>
            </div>

            {/* STDIO Configuration */}
            {mcpTransport === 'stdio' && (
              <>
                <Input
                  label="Command *"
                  value={mcpCommand}
                  onChange={(e) => setMcpCommand(e.target.value)}
                  placeholder="npx"
                  required
                />
                <Input
                  label="Arguments"
                  value={mcpArgs}
                  onChange={(e) => setMcpArgs(e.target.value)}
                  placeholder="-y @modelcontextprotocol/server-example"
                />
              </>
            )}

            {/* SSE/WS/HTTPSTREAM Configuration */}
            {(mcpTransport === 'sse' || mcpTransport === 'ws' || mcpTransport === 'httpstream') && (
              <Input
                label="Endpoint URL *"
                value={mcpEndpoint}
                onChange={(e) => setMcpEndpoint(e.target.value)}
                placeholder={mcpTransport === 'httpstream' ? "http://localhost:3000/stream" : "http://localhost:3000/sse"}
                type="url"
                required
              />
            )}

            {/* Timeout */}
            <Input
              label="Timeout (ms)"
              value={mcpTimeout}
              onChange={(e) => setMcpTimeout(e.target.value)}
              type="number"
              min={1000}
              max={300000}
            />

            {/* Header Variables */}
            <Textarea
              label="Header Variables (JSON)"
              value={mcpHeaders}
              onChange={(e) => setMcpHeaders(e.target.value)}
              placeholder='{\n  "Authorization": "Bearer your-token"\n}'
              rows={4}
              className="font-mono text-sm"
            />
          </div>
        )}

        {/* Extended Properties (JSON) */}
        <JsonEditor
          value={ext}
          onChange={setExt}
          placeholder='{\n  "key": "value"\n}'
        />

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-void-700">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : mode === 'create' ? 'Create Resource' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
