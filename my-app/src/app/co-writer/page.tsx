'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { PenTool, Loader2, Send, FileText, Minimize2, Maximize2 } from 'lucide-react';

export default function CoWriterPage() {
  const [text, setText] = useState('');
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [mode, setMode] = useState<'rewrite' | 'shorten' | 'expand'>('rewrite');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      let response;
      
      if (mode === 'rewrite') {
        response = await api.coWriter.rewrite({
          text: text.trim(),
          instruction: instruction.trim() || 'Improve the writing',
          use_rag: false,
        });
      } else if (mode === 'shorten') {
        response = await api.coWriter.shorten({
          text: text.trim(),
          instruction: instruction.trim() || 'Summarize and make it concise',
        });
      } else {
        response = await api.coWriter.expand({
          text: text.trim(),
          instruction: instruction.trim() || 'Expand with more details and explanations',
        });
      }

      if (response.data) {
        setResult(response.data);
      } else {
        setError('Failed to process text');
      }
    } catch (error: any) {
      console.error('Failed to process text:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to process text');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              Co-Writer
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              AI-powered writing assistant - rewrite, shorten, or expand your text
            </p>
          </div>

          {/* Mode Selector */}
          <div className="mb-6 bg-white dark:bg-zinc-900 rounded-lg shadow p-4">
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setMode('rewrite');
                  setResult(null);
                  setError(null);
                }}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'rewrite'
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                Rewrite
              </button>
              <button
                onClick={() => {
                  setMode('shorten');
                  setResult(null);
                  setError(null);
                }}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'shorten'
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                <Minimize2 className="inline h-4 w-4 mr-1" />
                Shorten
              </button>
              <button
                onClick={() => {
                  setMode('expand');
                  setResult(null);
                  setError(null);
                }}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === 'expand'
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                <Maximize2 className="inline h-4 w-4 mr-1" />
                Expand
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              {/* Instruction Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Instruction (optional)
                </label>
                <input
                  type="text"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  placeholder={
                    mode === 'rewrite'
                      ? 'e.g., "make it more formal", "simplify the language"'
                      : mode === 'shorten'
                      ? 'e.g., "summarize in 3 sentences"'
                      : 'e.g., "add more examples and explanations"'
                  }
                  disabled={loading}
                />
              </div>

              {/* Text Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Text to {mode}
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full px-4 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  rows={8}
                  placeholder={`Enter text to ${mode}...`}
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading || !text.trim()}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    {mode === 'rewrite' ? 'Rewrite' : mode === 'shorten' ? 'Shorten' : 'Expand'}
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg shadow p-6 mb-6">
              <div className="flex items-center text-red-800 dark:text-red-300">
                <span className="font-medium">Error: {error}</span>
              </div>
            </div>
          )}

          {result && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <FileText className="h-5 w-5 mr-2 text-green-600" />
                <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  Result
                </h2>
              </div>

              {mode === 'rewrite' && result.rewritten && (
                <div>
                  <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Rewritten Text:
                  </h3>
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800 p-4 rounded-md">
                      {result.rewritten}
                    </div>
                  </div>
                </div>
              )}

              {mode === 'shorten' && result.shortened && (
                <div>
                  <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Shortened Text:
                  </h3>
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800 p-4 rounded-md">
                      {result.shortened}
                    </div>
                  </div>
                </div>
              )}

              {mode === 'expand' && result.expanded && (
                <div>
                  <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Expanded Text:
                  </h3>
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800 p-4 rounded-md">
                      {result.expanded}
                    </div>
                  </div>
                </div>
              )}

              {result.original && (
                <div className="mt-6 pt-6 border-t border-zinc-200 dark:border-zinc-700">
                  <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Original Text:
                  </h3>
                  <div className="text-sm text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800 p-4 rounded-md">
                    {result.original}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
