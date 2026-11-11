/**
 * MCP Guide (Settings > MCP)
 *
 * Explains how to connect an agent to SkillHub's built-in MCP server
 * (Streamable HTTP, /api/v1/mcp) and gives copy-paste setup instructions for
 * the mainstream agents.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Copy, Key, Plug, ShieldCheck, Terminal, Wrench } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { getHealth } from '@/api/health';
import { cn } from '@/utils/cn';
import { copyText } from '@/utils/clipboard';

const ENV_VAR = 'SKILLHUB_API_KEY';
const KEY_PLACEHOLDER = '<YOUR_API_KEY>';

interface Step {
  title: string;
  description?: string;
  code: string;
}

interface Agent {
  id: string;
  label: string;
  /** Whether the config reads the key from the SKILLHUB_API_KEY env var. */
  usesEnvVar: boolean;
  steps: (url: string) => Step[];
  note?: string;
}

const json = (value: unknown) => JSON.stringify(value, null, 2);

const AGENTS: Agent[] = [
  {
    id: 'claude-code',
    label: 'Claude Code',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '命令行添加',
        description: '默认只对当前项目生效；加上 --scope user 对所有项目生效。',
        code: `claude mcp add --transport http skillhub ${url} --header "Authorization: Bearer $${ENV_VAR}"`,
      },
      {
        title: '或写入项目根目录的 .mcp.json（可随仓库共享）',
        code: json({
          mcpServers: {
            skillhub: {
              type: 'http',
              url,
              headers: { Authorization: `Bearer \${${ENV_VAR}}` },
            },
          },
        }),
      },
    ],
    note: '添加后运行 claude mcp list，或在会话中输入 /mcp 查看连接状态。',
  },
  {
    id: 'codex',
    label: 'Codex',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '命令行添加',
        code: `codex mcp add skillhub --url ${url} --bearer-token-env-var ${ENV_VAR}`,
      },
      {
        title: '或编辑 ~/.codex/config.toml',
        code: `[mcp_servers.skillhub]\nurl = "${url}"\nbearer_token_env_var = "${ENV_VAR}"`,
      },
    ],
    note: 'Codex 在启动时从环境变量读取密钥，配置文件里不保存密钥本身。',
  },
  {
    id: 'cursor',
    label: 'Cursor',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '编辑 ~/.cursor/mcp.json（全局）或 .cursor/mcp.json（项目）',
        code: json({
          mcpServers: {
            skillhub: {
              url,
              headers: { Authorization: `Bearer \${env:${ENV_VAR}}` },
            },
          },
        }),
      },
    ],
    note: '保存后在 Cursor Settings > MCP 中确认 skillhub 已启用。',
  },
  {
    id: 'vscode',
    label: 'VS Code',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '编辑 ~/.copilot/mcp-config.json（推荐）',
        code: json({
          mcpServers: {
            skillhub: {
              type: 'http',
              url,
              headers: { Authorization: `Bearer \${${ENV_VAR}}` },
            },
          },
        }),
      },
      {
        title: '旧版本：工作区的 .vscode/mcp.json',
        description: '首次启动该服务时 VS Code 会弹窗询问 API Key。',
        code: json({
          inputs: [
            {
              type: 'promptString',
              id: 'skillhub-key',
              description: 'SkillHub API Key',
              password: true,
            },
          ],
          servers: {
            skillhub: {
              type: 'http',
              url,
              headers: { Authorization: 'Bearer ${input:skillhub-key}' },
            },
          },
        }),
      },
    ],
  },
  {
    id: 'gemini',
    label: 'Gemini CLI',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '命令行添加',
        description: '默认写入当前项目；--scope user 写入用户级配置。',
        code: `gemini mcp add --transport http --header "Authorization: Bearer $${ENV_VAR}" skillhub ${url}`,
      },
      {
        title: '或编辑 ~/.gemini/settings.json',
        code: json({
          mcpServers: {
            skillhub: {
              httpUrl: url,
              headers: { Authorization: `Bearer \${${ENV_VAR}}` },
            },
          },
        }),
      },
    ],
    note: '注意字段名是 httpUrl（Streamable HTTP），url 字段表示的是旧的 SSE 传输。',
  },
  {
    id: 'windsurf',
    label: 'Windsurf',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '在 Cascade 的 MCP 面板中打开配置文件（mcp_config.json）并加入',
        code: json({
          mcpServers: {
            skillhub: {
              serverUrl: url,
              headers: { Authorization: `Bearer \${env:${ENV_VAR}}` },
            },
          },
        }),
      },
    ],
    note: '配置文件位置随版本不同（~/.config/devin/ 或 ~/.codeium/windsurf/），以面板里“打开 MCP 配置文件”打开的为准。',
  },
  {
    id: 'opencode',
    label: 'OpenCode',
    usesEnvVar: true,
    steps: (url) => [
      {
        title: '命令行添加',
        description: '加上 --global 对所有项目生效。',
        code: `opencode mcp add skillhub --url ${url} --header 'Authorization=Bearer {env:${ENV_VAR}}'`,
      },
      {
        title: '或编辑 opencode.json',
        code: json({
          mcp: {
            servers: {
              skillhub: {
                type: 'remote',
                url,
                oauth: false,
                headers: { Authorization: `Bearer {env:${ENV_VAR}}` },
              },
            },
          },
        }),
      },
    ],
    note: '旧版 OpenCode 把服务直接写在 mcp.<name> 下，如果上面的写法不生效请对照所用版本的文档。',
  },
  {
    id: 'cline',
    label: 'Cline',
    usesEnvVar: false,
    steps: (url) => [
      {
        title: '在 MCP Servers > Configure 中打开 cline_mcp_settings.json 并加入',
        code: json({
          mcpServers: {
            skillhub: {
              type: 'streamableHttp',
              url,
              headers: { Authorization: `Bearer ${KEY_PLACEHOLDER}` },
              disabled: false,
            },
          },
        }),
      },
    ],
    note: 'type 必须写 streamableHttp，省略时 Cline 会按旧的 SSE 方式连接。Cline 不支持环境变量占位符，需要直接填写密钥。',
  },
  {
    id: 'other',
    label: '其他',
    usesEnvVar: false,
    steps: (url) => [
      {
        title: '支持远程 MCP 的客户端：按下面三项填写',
        code: `Transport : Streamable HTTP\nURL       : ${url}\nHeader    : Authorization: Bearer ${KEY_PLACEHOLDER}`,
      },
      {
        title: '只支持 stdio 的客户端：用 mcp-remote 转接',
        code: json({
          mcpServers: {
            skillhub: {
              command: 'npx',
              args: ['mcp-remote', url, '--header', 'Authorization:${AUTH_HEADER}'],
              env: { AUTH_HEADER: `Bearer ${KEY_PLACEHOLDER}` },
            },
          },
        }),
      },
    ],
    note: 'SkillHub 地址是 http:// 而非 https:// 时，mcp-remote 需要在 args 里追加 --allow-http。',
  },
];

const TOOLS: Array<{ name: string; cli: string; description: string }> = [
  { name: 'list', cli: 'skillhub list [search_term] [-page N]', description: '列出或按名称搜索技能' },
  {
    name: 'install',
    cli: 'skillhub install <skill_name> [--outdir <path>]',
    description: '获取技能的 SKILL.md，由 Agent 写入本地目录',
  },
  { name: 'getme', cli: 'skillhub getme', description: '查看当前认证用户' },
  {
    name: 'third',
    cli: 'skillhub third <res_name> -method <M> [-inputs <json>]',
    description: '调用第三方 API 资源',
  },
  {
    name: 'gateway',
    cli: 'skillhub gateway <res_name> -method <M> -path <path> [-inputs <json>]',
    description: '调用网关资源的指定路径',
  },
  {
    name: 'mcp',
    cli: 'skillhub mcp <res_name> -mcptool <tool> [-inputs <json>]',
    description: '调用已注册 MCP 资源上的工具',
  },
  {
    name: 'composio_search',
    cli: 'skillhub composio search "<use case>" [--known-fields <k:v>]',
    description: '搜索 Composio 工具',
  },
  {
    name: 'composio_schema',
    cli: 'skillhub composio schema <TOOL_SLUG> ...',
    description: '获取 Composio 工具的输入 schema',
  },
  {
    name: 'composio_exec',
    cli: 'skillhub composio exec <TOOL_SLUG> [--inputs <json>] | --tools <json>',
    description: '执行 Composio 工具（单个或批量）',
  },
];

const CopyButton = ({ text, className }: { text: string; className?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (await copyText(text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={copied ? '已复制' : '复制'}
      className={cn(
        'flex items-center gap-1.5 px-2.5 py-1 rounded-md font-mono text-xs transition-all',
        'bg-cyber-primary/10 border border-cyber-primary/30 text-cyber-primary',
        'hover:bg-cyber-primary/20 hover:border-cyber-primary/50',
        className
      )}
    >
      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? '已复制' : '复制'}
    </button>
  );
};

const CodeBlock = ({ code }: { code: string }) => (
  <div className="bg-void-900/50 rounded-lg border border-void-700/50">
    {/* The button gets its own row: long one-line commands scroll sideways
        and would otherwise run underneath it. */}
    <div className="flex justify-end px-2 pt-2">
      <CopyButton text={code} />
    </div>
    <pre className="overflow-x-auto px-4 pb-4 pt-1 font-mono text-sm leading-relaxed text-cyber-secondary">
      <code>{code}</code>
    </pre>
  </div>
);

const SectionTitle = ({
  icon: Icon,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) => (
  <h3 className="flex items-center gap-2 mb-4 font-display text-lg font-semibold text-gray-100">
    <Icon className="w-5 h-5 text-cyber-primary" />
    {children}
  </h3>
);

export const McpGuidePage = () => {
  // Until the server reports its public URL, assume the page's own origin.
  const [baseUrl, setBaseUrl] = useState(window.location.origin);
  const [agentId, setAgentId] = useState(AGENTS[0].id);

  useEffect(() => {
    getHealth()
      .then((health) => {
        if (health.SKILLHUB_URL) {
          setBaseUrl(health.SKILLHUB_URL);
        }
      })
      .catch(console.error);
  }, []);

  const mcpUrl = `${baseUrl.replace(/\/+$/, '')}/api/v1/mcp`;
  const agent = AGENTS.find((item) => item.id === agentId) ?? AGENTS[0];
  const steps = agent.steps(mcpUrl);

  const exportCommand = `export ${ENV_VAR}=${KEY_PLACEHOLDER}`;
  const verifyCommand = [
    `curl -s ${mcpUrl} \\`,
    `  -H "Authorization: Bearer $${ENV_VAR}" \\`,
    '  -H "Content-Type: application/json" \\',
    '  -H "Accept: application/json, text/event-stream" \\',
    `  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`,
  ].join('\n');

  return (
    <div className="space-y-6">
      {/* Connection info */}
      <Card>
        <SectionTitle icon={Plug}>连接信息</SectionTitle>
        <p className="font-mono text-sm text-gray-400 mb-4">
          SkillHub 内置了标准 MCP 服务，Agent 可以直接通过 MCP 调用 skillhub CLI
          的全部能力，无需在本机安装 CLI。
        </p>

        <dl className="space-y-3 font-mono text-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
            <dt className="w-28 flex-shrink-0 text-gray-500">服务地址</dt>
            <dd className="flex flex-1 min-w-0 items-center gap-3">
              <code className="min-w-0 break-all text-cyber-secondary">{mcpUrl}</code>
              <CopyButton text={mcpUrl} className="flex-shrink-0" />
            </dd>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
            <dt className="w-28 flex-shrink-0 text-gray-500">传输方式</dt>
            <dd className="text-gray-300">Streamable HTTP</dd>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
            <dt className="w-28 flex-shrink-0 text-gray-500">认证方式</dt>
            <dd className="min-w-0 break-all text-gray-300">
              请求头 <code className="text-cyber-secondary">Authorization: Bearer {KEY_PLACEHOLDER}</code>
            </dd>
          </div>
        </dl>

        <div className="mt-4 pt-4 border-t border-void-700/50 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 mt-0.5 flex-shrink-0 text-cyber-primary" />
          <p className="font-mono text-xs text-gray-500 leading-relaxed">
            通过 MCP 调用资源时的权限与 CLI 完全一致，由资源的 ACL 规则决定。未携带 API Key
            时只能列出和安装 public 技能。
          </p>
        </div>
      </Card>

      {/* Setup */}
      <Card>
        <SectionTitle icon={Terminal}>安装到 Agent</SectionTitle>

        <ol className="space-y-6">
          <li>
            <p className="font-mono text-sm text-gray-300 mb-2">
              <span className="text-cyber-primary">1.</span> 准备 API Key
            </p>
            <p className="font-mono text-xs text-gray-500 mb-3 leading-relaxed">
              在{' '}
              <Link
                to="/settings?tab=api-keys"
                className="inline-flex items-center gap-1 text-cyber-primary hover:underline"
              >
                <Key className="w-3 h-3" />
                API Keys
              </Link>{' '}
              中创建一个密钥（以 sk_ 开头），并写入环境变量。与 CLI 使用同一个变量名，建议加入
              ~/.zshrc 或 ~/.bashrc。
            </p>
            <CodeBlock code={exportCommand} />
          </li>

          <li>
            <p className="font-mono text-sm text-gray-300 mb-3">
              <span className="text-cyber-primary">2.</span> 选择你的 Agent 并添加 MCP 服务
            </p>

            <div className="flex flex-wrap gap-2 mb-4" role="tablist" aria-label="Agent">
              {AGENTS.map((item) => {
                const isActive = item.id === agent.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    onClick={() => setAgentId(item.id)}
                    className={cn(
                      'px-3 py-1.5 rounded-md font-mono text-sm transition-all border',
                      isActive
                        ? 'bg-cyber-primary/10 text-cyber-primary border-cyber-primary/30'
                        : 'text-gray-400 border-void-700/50 hover:text-gray-200 hover:bg-void-800/50'
                    )}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>

            <div className="space-y-4" role="tabpanel">
              {steps.map((step) => (
                <div key={step.title}>
                  <p className="font-mono text-sm text-gray-400 mb-1">{step.title}</p>
                  {step.description && (
                    <p className="font-mono text-xs text-gray-500 mb-2">{step.description}</p>
                  )}
                  <CodeBlock code={step.code} />
                </div>
              ))}

              {!agent.usesEnvVar && (
                <p className="font-mono text-xs text-cyber-warning leading-relaxed">
                  这里需要把 {KEY_PLACEHOLDER} 替换成真实的 API Key，请不要把含密钥的配置文件提交到代码仓库。
                </p>
              )}
              {agent.note && (
                <p className="font-mono text-xs text-gray-500 leading-relaxed">{agent.note}</p>
              )}
            </div>
          </li>

          <li>
            <p className="font-mono text-sm text-gray-300 mb-2">
              <span className="text-cyber-primary">3.</span> 验证连接
            </p>
            <p className="font-mono text-xs text-gray-500 mb-3 leading-relaxed">
              重启 Agent 后让它调用 getme 工具，返回你的用户信息即表示连接和认证都正常。也可以先用
              curl 直接检查服务，正常时返回工具列表，密钥无效时返回 401。
            </p>
            <CodeBlock code={verifyCommand} />
          </li>
        </ol>
      </Card>

      {/* Tools */}
      <Card>
        <SectionTitle icon={Wrench}>可用工具</SectionTitle>
        <p className="font-mono text-sm text-gray-400 mb-4">
          每个工具对应一条 skillhub CLI 命令，参数名与 CLI 保持一致；-token 由连接的 Authorization
          请求头代替。
        </p>

        <div className="overflow-x-auto">
          <table className="w-full font-mono text-sm">
            <thead>
              <tr className="border-b border-void-700 text-left text-xs text-gray-500">
                <th className="py-2 pr-4 font-normal">工具</th>
                <th className="py-2 pr-4 font-normal">说明</th>
                <th className="py-2 font-normal">对应 CLI</th>
              </tr>
            </thead>
            <tbody>
              {TOOLS.map((tool) => (
                <tr key={tool.name} className="border-b border-void-700/50 last:border-0 align-top">
                  <td className="py-2.5 pr-4 whitespace-nowrap text-cyber-primary">{tool.name}</td>
                  <td className="py-2.5 pr-4 text-gray-300">{tool.description}</td>
                  <td className="py-2.5 text-xs text-gray-500">{tool.cli}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default McpGuidePage;
