import React, { useState, useEffect } from 'react';
import { Code, X, Check, AlertCircle } from 'lucide-react';

interface JsonEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export const JsonEditor: React.FC<JsonEditorProps> = ({
  value,
  onChange,
  placeholder = '{\n  "key": "value"\n}',
  className = '',
}) => {
  const [isValid, setIsValid] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!value.trim()) {
      setIsValid(true);
      setError('');
      return;
    }

    try {
      JSON.parse(value);
      setIsValid(true);
      setError('');
    } catch (err) {
      setIsValid(false);
      setError(err instanceof Error ? err.message : 'Invalid JSON');
    }
  }, [value]);

  const handleFormat = () => {
    if (!value.trim()) return;

    try {
      const parsed = JSON.parse(value);
      const formatted = JSON.stringify(parsed, null, 2);
      onChange(formatted);
    } catch (err) {
      // Don't change the value if it's invalid
      console.error('Cannot format invalid JSON:', err);
    }
  };

  const handleClear = () => {
    onChange('');
  };

  const getStatusIcon = () => {
    if (!value.trim()) return null;
    return isValid ? (
      <Check className="w-5 h-5 text-cyber-primary" />
    ) : (
      <AlertCircle className="w-5 h-5 text-cyber-accent" />
    );
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
          JSON Data
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleFormat}
            disabled={!value.trim() || !isValid}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-gray-300 bg-void-800 border border-void-600 rounded hover:bg-void-700 hover:text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            title="Format JSON (pretty print)"
          >
            <Code className="w-3 h-3" />
            Format
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={!value.trim()}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-gray-300 bg-void-800 border border-void-600 rounded hover:bg-void-700 hover:text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            title="Clear JSON"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
          {getStatusIcon()}
        </div>
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-3 font-mono text-sm border rounded-lg focus:outline-none focus:border-cyber-primary bg-void-900/50 text-gray-200 placeholder:text-gray-600 min-h-[200px] transition-colors"
        spellCheck={false}
      />

      {!isValid && error && (
        <div className="mt-2 p-2 text-xs text-cyber-accent bg-cyber-accent/10 border border-cyber-accent/30 rounded">
          <strong>JSON Error:</strong> {error}
        </div>
      )}
    </div>
  );
};
