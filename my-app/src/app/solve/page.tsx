'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Brain, Send, Loader2, BookOpen, FileText } from 'lucide-react';
import SaveToNotebook from '@/components/SaveToNotebook';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
}

interface Citation {
  id: number;
  document_id: string;
  filename: string;
  page_start: number | string;
  page_end: number | string;
  snippet: string;
  similarity?: number;
}

interface RAGResponse {
  success: boolean;
  answer: string;
  citations: Citation[];
  chunks_retrieved: number;
  question: string;
  error?: string;
}

export default function SolvePage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKB, setSelectedKB] = useState<string>('');
  const [ragResult, setRagResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    try {
      const response = await api.knowledgeBase.list();
      const kbs = response.data.knowledge_bases || [];
      setKnowledgeBases(kbs);
      // Auto-select first KB if available
      if (kbs.length > 0 && !selectedKB) {
        setSelectedKB(kbs[0].id);
      }
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    if (!selectedKB) {
      setError('Please select a knowledge base first');
      return;
    }

    setLoading(true);
    setRagResult(null);
    setError(null);

    try {
      const response = await api.knowledgeBase.ask(selectedKB, {
        question: question.trim(),
        top_k: 5,
        threshold: 0.3, // Lower threshold to find more results
      });
      
      if (response.data.success) {
        setRagResult(response.data);
      } else {
        setError(response.data.error || 'Failed to get answer');
      }
    } catch (error: any) {
      console.error('Failed to ask question:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to get answer');
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
              Problem Solver
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Get step-by-step solutions to your questions
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              {/* Knowledge Base Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  <BookOpen className="inline h-4 w-4 mr-1" />
                  Knowledge Base
                </label>
                {knowledgeBases.length === 0 ? (
                  <div className="text-sm text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800 px-4 py-3 rounded-md border border-zinc-200 dark:border-zinc-700">
                    No knowledge bases available. <a href="/knowledge-base" className="text-blue-600 dark:text-blue-400 hover:underline">Create one first</a>
                  </div>
                ) : (
                  <select
                    value={selectedKB}
                    onChange={(e) => setSelectedKB(e.target.value)}
                    className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                    disabled={loading}
                  >
                    {knowledgeBases.map((kb) => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name} ({kb.document_count} documents)
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Question Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Ask a Question
                </label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full px-4 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  rows={4}
                  placeholder="Enter your question about the knowledge base..."
                  disabled={loading || knowledgeBases.length === 0}
                />
              </div>

              <button
                type="submit"
                disabled={loading || !question.trim() || !selectedKB || knowledgeBases.length === 0}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Ask Question
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

          {loading && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center text-zinc-600 dark:text-zinc-400">
                <Brain className="h-5 w-5 mr-2 animate-pulse" />
                <span>Searching knowledge base and generating answer...</span>
              </div>
            </div>
          )}

          {ragResult && ragResult.success && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  Answer
                </h2>
                <SaveToNotebook
                  itemType="solve"
                  title={question || 'Question from Solve'}
                  content={{
                    question: question,
                    answer: ragResult.answer,
                    citations: ragResult.citations,
                    knowledge_base_id: selectedKB,
                  }}
                />
              </div>
              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  {ragResult.answer}
                </div>
              </div>

              {ragResult.citations && ragResult.citations.length > 0 && (
                <div className="mt-6 pt-6 border-t border-zinc-200 dark:border-zinc-700">
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-3">
                    Citations ({ragResult.citations.length})
                  </h3>
                  <div className="space-y-3">
                    {ragResult.citations.map((citation) => (
                      <div
                        key={citation.id}
                        className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4 border border-zinc-200 dark:border-zinc-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold">
                              [{citation.id}]
                            </span>
                            <span className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                              {citation.filename}
                            </span>
                          </div>
                          <span className="text-xs text-zinc-500 dark:text-zinc-400">
                            {citation.page_start === citation.page_end
                              ? `Page ${citation.page_start}`
                              : `Pages ${citation.page_start}-${citation.page_end}`}
                          </span>
                        </div>
                        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-2 line-clamp-2">
                          {citation.snippet}
                        </p>
                        {citation.similarity && (
                          <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                            Similarity: {(citation.similarity * 100).toFixed(1)}%
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {ragResult.chunks_retrieved && (
                <div className="mt-4 text-xs text-zinc-500 dark:text-zinc-400">
                  Retrieved {ragResult.chunks_retrieved} relevant chunk(s) from knowledge base
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


