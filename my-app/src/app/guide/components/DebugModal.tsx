'use client';

import { useState } from 'react';
import { X, Loader2 } from 'lucide-react';

interface DebugModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFix: (description: string) => Promise<string>;
}

export function DebugModal({ isOpen, onClose, onFix }: DebugModalProps) {
  const [description, setDescription] = useState('');
  const [fixing, setFixing] = useState(false);
  const [fixedHtml, setFixedHtml] = useState('');

  if (!isOpen) return null;

  const handleFix = async () => {
    if (!description.trim()) return;

    setFixing(true);
    try {
      const result = await onFix(description);
      setFixedHtml(result);
    } catch (error) {
      console.error('Failed to fix HTML:', error);
      alert('Failed to fix HTML. Please try again.');
    } finally {
      setFixing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Debug HTML
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Describe the issue:
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what's wrong with the HTML..."
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 min-h-[100px]"
            />
          </div>

          <button
            onClick={handleFix}
            disabled={!description.trim() || fixing}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          >
            {fixing ? (
              <span className="flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Fixing...
              </span>
            ) : (
              'Fix HTML'
            )}
          </button>

          {fixedHtml && (
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Fixed HTML:
              </label>
              <pre className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-xs overflow-x-auto max-h-[300px]">
                {fixedHtml}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

