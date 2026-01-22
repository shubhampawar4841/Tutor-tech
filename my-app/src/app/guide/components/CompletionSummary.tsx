'use client';

import { CheckCircle2 } from 'lucide-react';

interface CompletionSummaryProps {
  summary: string;
}

export function CompletionSummary({ summary }: CompletionSummaryProps) {
  // Simple markdown to HTML converter (basic)
  const markdownToHtml = (text: string) => {
    return text
      .split('\n')
      .map(line => {
        // Headers
        if (line.startsWith('### ')) {
          return `<h3 class="text-lg font-semibold mt-4 mb-2 text-slate-900 dark:text-slate-100">${line.substring(4)}</h3>`;
        }
        if (line.startsWith('## ')) {
          return `<h2 class="text-xl font-semibold mt-6 mb-3 text-slate-900 dark:text-slate-100">${line.substring(3)}</h2>`;
        }
        if (line.startsWith('# ')) {
          return `<h1 class="text-2xl font-bold mt-6 mb-4 text-slate-900 dark:text-slate-100">${line.substring(2)}</h1>`;
        }
        // Bold
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic
        line = line.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Lists
        if (line.trim().startsWith('- ')) {
          return `<li class="ml-4 mb-1">${line.substring(2)}</li>`;
        }
        // Empty line
        if (line.trim() === '') {
          return '<br />';
        }
        return `<p class="mb-3 text-slate-700 dark:text-slate-300 leading-relaxed">${line}</p>`;
      })
      .join('');
  };

  return (
    <div className="flex-1 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-8 overflow-y-auto">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Learning Completed!
          </h1>
        </div>

        <div className="text-slate-700 dark:text-slate-300">
          {summary ? (
            <div
              className="prose dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: markdownToHtml(summary) }}
            />
          ) : (
            <p className="text-slate-600 dark:text-slate-400">
              Congratulations! You've completed all knowledge points in this learning guide.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

