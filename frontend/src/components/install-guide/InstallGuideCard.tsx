/**
 * Install Guide Card Component
 *
 * Provides installation instructions for SkillHub CLI with two modes:
 * - Agent mode: Natural language instruction for AI agents
 * - Human mode: Direct curl command for users
 */

import { useState, useEffect } from 'react';
import { Copy, Check, Bot, User, Terminal } from 'lucide-react';
import { Card, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { getHealth, HealthResponse } from '@/api/health';

/**
 * Safely join URL parts, avoiding duplicate slashes
 */
const joinUrl = (...parts: string[]): string => {
  return parts
    .map(part => part.replace(/^\/+|\/+$/g, '')) // Remove leading/trailing slashes
    .filter(part => part.length > 0) // Remove empty parts
    .join('/');
};

export const InstallGuideCard = () => {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then(setHealthData)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const handleCopy = async (text: string) => {
    try {
      // 优先使用现代 Clipboard API (需要安全上下文: HTTPS 或 localhost)
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // 降级到传统方法: 使用 execCommand (兼容非安全上下文)
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
          const successful = document.execCommand('copy');
          if (!successful) {
            throw new Error('execCommand failed');
          }
        } catch (err) {
          console.error('Copy failed:', err);
          throw new Error('复制功能不可用，请手动选择复制');
        } finally {
          document.body.removeChild(textArea);
        }
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy error:', error);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center gap-3 text-gray-500">
            <Terminal className="w-5 h-5 animate-pulse" />
            <span className="font-mono text-sm">Loading...</span>
          </div>
        </div>
      </Card>
    );
  }

  if (!healthData) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <p className="font-mono text-sm text-cyber-accent">
            Unable to load installation guide
          </p>
        </div>
      </Card>
    );
  }

  const baseUrl = healthData.SKILLHUB_URL;

  // Build URLs using the safe join function
  const installUrl = joinUrl(baseUrl, 'api', 'v1', 'script', 'install');
  const bashUrl = joinUrl(baseUrl, 'api', 'v1', 'script', 'bash');

  // Agent mode: Natural language instruction for AI agents
  const agentText = `从 ${installUrl} 获取 install.md 文件，并按照指引完成安装`;

  // Human mode: Direct curl command for users
  const humanCommand = `curl -s ${bashUrl} -o skillhub.sh && chmod +x skillhub.sh`;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-lg font-semibold text-gray-100">
          安装 SkillHub CLI
        </h3>
        <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
          <span className="w-2 h-2 rounded-full bg-cyber-primary animate-pulse" />
          Online
        </div>
      </div>

      <p className="font-mono text-sm text-gray-400 mb-4">
        选择适合你的安装方式
      </p>

      <Tabs defaultValue="agent">
        <TabsList className="w-full">
          <TabsTrigger value="agent" className="flex-1 flex items-center justify-center gap-2">
            <Bot className="w-4 h-4" />
            Agent
          </TabsTrigger>
          <TabsTrigger value="human" className="flex-1 flex items-center justify-center gap-2">
            <User className="w-4 h-4" />
            Human
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agent">
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700/50">
            <div className="flex items-start gap-2 mb-3">
              <Bot className="w-5 h-5 text-cyber-secondary mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-mono text-sm text-gray-300 leading-relaxed">
                  {agentText}
                </p>
              </div>
            </div>
            <button
              onClick={() => handleCopy(agentText)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-cyber-primary/10 border border-cyber-primary/30 text-cyber-primary hover:bg-cyber-primary/20 hover:border-cyber-primary/50 transition-all font-mono text-sm"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? '已复制' : '复制指令'}
            </button>
          </div>
        </TabsContent>

        <TabsContent value="human">
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700/50">
            <div className="flex items-start gap-2 mb-3">
              <Terminal className="w-5 h-5 text-cyber-accent mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <code className="font-mono text-sm text-cyber-secondary block leading-relaxed break-all">
                  {humanCommand}
                </code>
              </div>
            </div>
            <button
              onClick={() => handleCopy(humanCommand)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-cyber-primary/10 border border-cyber-primary/30 text-cyber-primary hover:bg-cyber-primary/20 hover:border-cyber-primary/50 transition-all font-mono text-sm"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? '已复制' : '复制命令'}
            </button>
          </div>
        </TabsContent>
      </Tabs>

      <div className="mt-4 pt-4 border-t border-void-700/50">
        <p className="font-mono text-xs text-gray-500 text-center">
          安装后需要配置 SKILLHUB_API_KEY 环境变量,手动下载skillhub.sh用户建议移动到/usr/local/bin目录下
        </p>
      </div>
    </Card>
  );
};
