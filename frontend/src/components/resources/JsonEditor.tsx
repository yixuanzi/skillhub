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

  const getBorderColor = () => {
    if (!value.trim()) return 'border-gray-300 dark:border-gray-600';
    return isValid
      ? 'border-green-500 dark:border-green-400'
      : 'border-red-500 dark:border-red-400';
  };

  const getStatusIcon = () => {
    if (!value.trim()) return null;
    return isValid ? (
      <Check className="w-5 h-5 text-green-500 dark:text-green-400" />
    ) : (
      <AlertCircle className="w-5 h-5 text-red-500 dark:text-red-400" />
    );
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          JSON Data
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleFormat}
            disabled={!value.trim() || !isValid}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Format JSON (pretty print)"
          >
            <Code className="w-3 h-3" />
            Format
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={!value.trim()}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
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
        className={`w-full px-3 py-2 font-mono text-sm border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 ${getBorderColor()} min-h-[200px]`}
        spellCheck={false}
      />

      {!isValid && error && (
        <div className="mt-2 p-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
          <strong>JSON Error:</strong> {error}
        </div>
      )}
    </div>
  );
};
