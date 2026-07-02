import type { AnchorHTMLAttributes, HTMLAttributes } from 'react';
import { BookOpen, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card } from '@/components/ui/Card';
import userManualMarkdown from '../../../../docs/user-manual-zh.md?raw';

const mdHeadingStyles = {
  h1: 'font-display text-3xl font-bold text-gray-100',
  h2: 'font-display text-2xl font-semibold text-cyber-primary border-b border-void-700 pb-3 mt-10',
  h3: 'font-display text-xl font-semibold text-gray-100 mt-8',
};

const isExternalHref = (href?: string) => /^https?:\/\//i.test(href || '');

const InlineCode = ({ children, className, ...props }: HTMLAttributes<HTMLElement>) => (
  <code
    className={[
      'rounded border border-void-700 bg-void-900 px-1.5 py-0.5 font-mono text-[0.9em] text-cyber-secondary',
      className,
    ].filter(Boolean).join(' ')}
    {...props}
  >
    {children}
  </code>
);

const LinkRenderer = ({ href, children, className, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) => {
  if (!href) {
    return <span className={className}>{children}</span>;
  }

  if (isExternalHref(href)) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer noopener"
        className={[
          'font-medium text-cyber-secondary underline decoration-cyber-secondary/40 underline-offset-4 transition-colors hover:text-cyber-primary',
          className,
        ].filter(Boolean).join(' ')}
        {...props}
      >
        {children}
      </a>
    );
  }

  return (
    <span
      className={[
        'font-medium text-gray-400 underline decoration-dotted underline-offset-4',
        className,
      ].filter(Boolean).join(' ')}
    >
      {children}
    </span>
  );
};

export const UserManualPage = () => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="rounded-lg border border-cyber-primary/30 bg-cyber-primary/10 p-2.5">
          <BookOpen className="h-5 w-5 text-cyber-primary" />
        </div>
        <div>
          <h2 className="font-display text-xl font-semibold text-gray-100">User Manual</h2>
          <p className="font-mono text-sm text-gray-500">
            Read the current SkillHub user manual rendered from the repository documentation.
          </p>
        </div>
      </div>

      <Card className="border-cyber-secondary/30 bg-cyber-secondary/5 p-4">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-cyber-secondary" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-cyber-secondary">About This Page</p>
            <p className="text-xs text-gray-400">
              This tab displays the repository file <code className="font-mono text-cyber-secondary">docs/user-manual-zh.md</code>.
              Update that document to keep the in-app manual in sync.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-0">
        <div className="max-h-[72vh] overflow-y-auto px-6 py-8 sm:px-8">
          <div className="space-y-4 text-sm leading-7 text-gray-300">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className={mdHeadingStyles.h1}>{children}</h1>,
                h2: ({ children }) => <h2 className={mdHeadingStyles.h2}>{children}</h2>,
                h3: ({ children }) => <h3 className={mdHeadingStyles.h3}>{children}</h3>,
                p: ({ children }) => <p className="text-gray-300">{children}</p>,
                ul: ({ children }) => <ul className="list-disc space-y-2 pl-6 text-gray-300">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal space-y-2 pl-6 text-gray-300">{children}</ol>,
                li: ({ children }) => <li className="marker:text-cyber-primary">{children}</li>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-cyber-secondary/60 bg-void-900/60 px-4 py-3 text-gray-300">
                    {children}
                  </blockquote>
                ),
                hr: () => <hr className="my-8 border-void-700" />,
                a: LinkRenderer,
                table: ({ children }) => (
                  <div className="overflow-x-auto rounded-lg border border-void-700">
                    <table className="min-w-full border-collapse text-left text-sm">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-void-900/90 text-gray-100">{children}</thead>,
                tbody: ({ children }) => <tbody className="divide-y divide-void-700 bg-void-900/40">{children}</tbody>,
                tr: ({ children }) => <tr className="align-top">{children}</tr>,
                th: ({ children }) => (
                  <th className="border-b border-void-700 px-4 py-3 font-mono text-xs uppercase tracking-wider text-cyber-primary">
                    {children}
                  </th>
                ),
                td: ({ children }) => <td className="px-4 py-3 text-sm text-gray-300">{children}</td>,
                code: ({ className, children, ...props }) => {
                  const isBlockCode = Boolean(className?.includes('language-')) || String(children).includes('\n');

                  return isBlockCode ? (
                    <code
                      className={[
                        'block overflow-x-auto rounded-lg bg-void-950 px-4 py-4 font-mono text-sm leading-6 text-cyber-primary',
                        className,
                      ].filter(Boolean).join(' ')}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <InlineCode className={className} {...props}>
                      {children}
                    </InlineCode>
                  );
                },
                pre: ({ children }) => <pre className="overflow-x-auto">{children}</pre>,
              }}
            >
              {userManualMarkdown}
            </ReactMarkdown>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default UserManualPage;
