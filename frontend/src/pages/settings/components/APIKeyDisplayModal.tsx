import { useState, useEffect } from 'react';
import { Copy, Check, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { cn } from '@/utils/cn';

interface APIKeyDisplayModalProps {
  apiKey: string;
  onClose: () => void;
}

export const APIKeyDisplayModal = ({ apiKey, onClose }: APIKeyDisplayModalProps) => {
  const [copied, setCopied] = useState(false);
  const [visible, setVisible] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Hide key when modal closes
  useEffect(() => {
    setVisible(false);
  }, [apiKey]);

  // Auto-hide on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const maskedKey = apiKey.slice(0, 10) + '•'.repeat(Math.max(0, apiKey.length - 10));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <Card className="w-full max-w-lg p-6 animate-slide-in">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-cyber-primary/10 border border-cyber-primary/30">
            {copied ? (
              <Check className="w-5 h-5 text-cyber-primary" />
            ) : (
              <Copy className="w-5 h-5 text-cyber-primary" />
            )}
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold text-gray-100">
              {copied ? 'Key Copied!' : 'API Key Created'}
            </h2>
            <p className="text-sm text-gray-500">
              {copied ? 'Your key has been copied to the clipboard' : 'Copy this key now'}
            </p>
          </div>
        </div>

        {/* Key Display */}
        <div className="mb-6">
          <div className="relative">
            <div className={cn(
              'p-4 rounded-lg border transition-all duration-200',
              'bg-void-900/80 border-void-700 font-mono text-sm break-all',
              copied && 'border-cyber-primary/50 bg-cyber-primary/5'
            )}>
              {visible ? apiKey : maskedKey}
            </div>
            <button
              type="button"
              onClick={() => setVisible(!visible)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-gray-500 hover:text-gray-300 transition-colors"
              title={visible ? 'Hide key' : 'Show key'}
            >
              {visible ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Warning */}
        <Card className="p-4 border-cyber-accent/30 bg-cyber-accent/5 mb-6">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-cyber-accent flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-cyber-accent">Important!</p>
              <p className="text-xs text-gray-400">
                You won't be able to see this key again after closing this dialog.
                Make sure to copy and store it securely in a password manager or secure vault.
              </p>
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button
            variant={copied ? 'secondary' : 'primary'}
            onClick={handleCopy}
            className="flex-1 group"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 mr-2" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-2 transition-transform group-hover:scale-110" />
                Copy Key to Clipboard
              </>
            )}
          </Button>
          <Button
            variant="ghost"
            onClick={onClose}
            className="flex-1"
          >
            I've Saved It
          </Button>
        </div>
      </Card>
    </div>
  );
};
