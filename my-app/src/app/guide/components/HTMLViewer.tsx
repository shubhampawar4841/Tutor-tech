'use client';

import { useEffect, useRef } from 'react';
import { Wrench } from 'lucide-react';

interface HTMLViewerProps {
  html: string;
  currentIndex: number;
  loadingMessage?: string;
  onOpenDebugModal: () => void;
}

export function HTMLViewer({ html, currentIndex, loadingMessage, onOpenDebugModal }: HTMLViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (iframeRef.current && html) {
      const iframe = iframeRef.current;
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      
      if (doc) {
        doc.open();
        doc.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <style>
                * {
                  margin: 0;
                  padding: 0;
                  box-sizing: border-box;
                }
                body {
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                  line-height: 1.6;
                  color: #1e293b;
                  background: #ffffff;
                  padding: 2rem;
                  max-width: 1200px;
                  margin: 0 auto;
                }
                .dark body {
                  background: #0f172a;
                  color: #e2e8f0;
                }
                .guide-content {
                  animation: fadeIn 0.3s ease-in;
                }
                @keyframes fadeIn {
                  from { opacity: 0; transform: translateY(10px); }
                  to { opacity: 1; transform: translateY(0); }
                }
                .guide-header h1 {
                  font-size: 2rem;
                  font-weight: 700;
                  margin-bottom: 0.5rem;
                  color: #1e293b;
                }
                .dark .guide-header h1 {
                  color: #e2e8f0;
                }
                .guide-description {
                  font-size: 1.1rem;
                  color: #64748b;
                  margin-bottom: 1rem;
                }
                .dark .guide-description {
                  color: #94a3b8;
                }
                .guide-progress {
                  font-size: 0.875rem;
                  color: #64748b;
                  margin-bottom: 2rem;
                }
                .guide-key-points {
                  background: #f1f5f9;
                  border-left: 4px solid #3b82f6;
                  padding: 1.5rem;
                  margin: 2rem 0;
                  border-radius: 0.5rem;
                }
                .dark .guide-key-points {
                  background: #1e293b;
                  border-left-color: #60a5fa;
                }
                .guide-key-points h2 {
                  font-size: 1.25rem;
                  font-weight: 600;
                  margin-bottom: 1rem;
                }
                .guide-key-points ul {
                  list-style: disc;
                  margin-left: 1.5rem;
                }
                .guide-key-points li {
                  margin-bottom: 0.5rem;
                }
                .guide-main-content {
                  margin: 2rem 0;
                }
                .guide-main-content p {
                  margin-bottom: 1rem;
                  line-height: 1.8;
                }
                .guide-section {
                  margin: 2rem 0;
                  padding: 1.5rem;
                  border-radius: 0.5rem;
                }
                .guide-section h2 {
                  font-size: 1.5rem;
                  font-weight: 600;
                  margin-bottom: 1rem;
                }
                .guide-intuition {
                  background: #fef3c7;
                  border-left: 4px solid #f59e0b;
                }
                .dark .guide-intuition {
                  background: #451a03;
                  border-left-color: #fbbf24;
                }
                .guide-intuition h2 {
                  color: #92400e;
                }
                .dark .guide-intuition h2 {
                  color: #fbbf24;
                }
                .guide-intuition-text {
                  font-size: 1.1rem;
                  line-height: 1.8;
                  font-style: italic;
                }
                .guide-definition {
                  background: #dbeafe;
                  border-left: 4px solid #3b82f6;
                }
                .dark .guide-definition {
                  background: #1e3a5f;
                  border-left-color: #60a5fa;
                }
                .guide-definition h2 {
                  color: #1e40af;
                }
                .dark .guide-definition h2 {
                  color: #93c5fd;
                }
                .guide-mechanism {
                  background: #e0e7ff;
                  border-left: 4px solid #6366f1;
                }
                .dark .guide-mechanism {
                  background: #312e81;
                  border-left-color: #818cf8;
                }
                .guide-mechanism h2 {
                  color: #4338ca;
                }
                .dark .guide-mechanism h2 {
                  color: #a5b4fc;
                }
                .guide-mechanism-content p {
                  margin-bottom: 1rem;
                  line-height: 1.8;
                }
                .guide-importance {
                  background: #dcfce7;
                  border-left: 4px solid #22c55e;
                }
                .dark .guide-importance {
                  background: #14532d;
                  border-left-color: #4ade80;
                }
                .guide-importance h2 {
                  color: #15803d;
                }
                .dark .guide-importance h2 {
                  color: #86efac;
                }
                .guide-examples {
                  background: #f3e8ff;
                  border-left: 4px solid #a855f7;
                }
                .dark .guide-examples {
                  background: #581c87;
                  border-left-color: #c084fc;
                }
                .guide-examples h2 {
                  color: #7e22ce;
                }
                .dark .guide-examples h2 {
                  color: #d8b4fe;
                }
                .guide-examples-list {
                  list-style: disc;
                  margin-left: 1.5rem;
                }
                .guide-examples-list li {
                  margin-bottom: 0.75rem;
                  line-height: 1.7;
                }
                .guide-mistakes {
                  background: #fee2e2;
                  border-left: 4px solid #ef4444;
                }
                .dark .guide-mistakes {
                  background: #7f1d1d;
                  border-left-color: #f87171;
                }
                .guide-mistakes h2 {
                  color: #dc2626;
                }
                .dark .guide-mistakes h2 {
                  color: #fca5a5;
                }
                .guide-mistakes-list {
                  list-style: disc;
                  margin-left: 1.5rem;
                }
                .guide-mistakes-list li {
                  margin-bottom: 0.75rem;
                  line-height: 1.7;
                }
                .guide-questions {
                  background: #fef3c7;
                  border: 1px solid #fbbf24;
                  padding: 1.5rem;
                  margin: 2rem 0;
                  border-radius: 0.5rem;
                }
                .dark .guide-questions {
                  background: #451a03;
                  border-color: #f59e0b;
                }
                .guide-remedial {
                  background: #dbeafe;
                  border: 2px solid #3b82f6;
                  padding: 1.5rem;
                  margin: 2rem 0;
                  border-radius: 0.5rem;
                }
                .dark .guide-remedial {
                  background: #1e3a5f;
                  border-color: #60a5fa;
                }
                .guide-remedial h2 {
                  font-size: 1.5rem;
                  font-weight: 600;
                  margin-bottom: 1rem;
                  color: #1e40af;
                }
                .dark .guide-remedial h2 {
                  color: #93c5fd;
                }
                .remedial-item {
                  margin-bottom: 1.5rem;
                  padding-bottom: 1rem;
                  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
                }
                .remedial-item:last-child {
                  border-bottom: none;
                }
                .remedial-section {
                  margin: 1rem 0;
                }
                .remedial-section h4 {
                  font-size: 1.1rem;
                  font-weight: 600;
                  margin-bottom: 0.5rem;
                  color: #1e40af;
                }
                .dark .remedial-section h4 {
                  color: #93c5fd;
                }
                .remedial-section ol, .remedial-section ul {
                  margin-left: 1.5rem;
                  margin-top: 0.5rem;
                }
                .remedial-section li {
                  margin-bottom: 0.5rem;
                }
                .guide-questions h2 {
                  font-size: 1.25rem;
                  font-weight: 600;
                  margin-bottom: 1rem;
                }
                .question-item {
                  margin-bottom: 1.5rem;
                  padding-bottom: 1rem;
                  border-bottom: 1px solid rgba(0,0,0,0.1);
                }
                .question-item:last-child {
                  border-bottom: none;
                }
                .question-item h3 {
                  font-size: 1rem;
                  font-weight: 600;
                  margin-bottom: 0.5rem;
                }
                .hint {
                  font-size: 0.875rem;
                  color: #64748b;
                  margin-top: 0.5rem;
                  font-style: italic;
                }
                .dark .hint {
                  color: #94a3b8;
                }
              </style>
            </head>
            <body class="${document.documentElement.classList.contains('dark') ? 'dark' : ''}">
              ${html}
            </body>
          </html>
        `);
        doc.close();
      }
    }
  }, [html, currentIndex]);

  if (!html) {
    return (
      <div className="flex-1 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-400 dark:text-slate-500 mb-2">
            {loadingMessage || 'Loading content...'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden relative">
      <button
        onClick={onOpenDebugModal}
        className="absolute top-4 right-4 z-10 p-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg shadow-sm hover:bg-slate-50 dark:hover:bg-slate-600 transition-all"
        title="Debug HTML"
      >
        <Wrench className="w-4 h-4 text-slate-600 dark:text-slate-300" />
      </button>
      <iframe
        ref={iframeRef}
        className="w-full h-full border-0"
        title="Learning Content"
        sandbox="allow-same-origin"
      />
    </div>
  );
}

