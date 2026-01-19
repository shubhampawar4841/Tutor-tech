'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Lightbulb, Loader2, Send, BookOpen, Sparkles } from 'lucide-react';

interface Notebook {
  id: string;
  name: string;
  description: string;
  item_count: number;
}

interface Idea {
  title: string;
  description: string;
  key_concepts: string[];
  difficulty: string;
}

export default function IdeaGenPage() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [selectedNotebooks, setSelectedNotebooks] = useState<string[]>([]);
  const [domain, setDomain] = useState('');
  const [ideaType, setIdeaType] = useState('research');
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotebooks();
  }, []);

  const loadNotebooks = async () => {
    try {
      const response = await api.notebook.list();
      const notebooksData = response.data.notebooks || [];
      setNotebooks(notebooksData);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedNotebooks.length && !domain.trim()) {
      setError('Please select notebooks or enter a domain');
      return;
    }

    setLoading(true);
    setIdeas([]);
    setError(null);

    try {
      const response = await api.ideagen.generate({
        notebook_ids: selectedNotebooks.length > 0 ? selectedNotebooks : undefined,
        domain: domain.trim() || undefined,
        count: count,
        idea_type: ideaType,
      });

      if (response.data.success) {
        setIdeas(response.data.ideas || []);
      } else {
        setError(response.data.error || 'Failed to generate ideas');
      }
    } catch (error: any) {
      console.error('Failed to generate ideas:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to generate ideas');
    } finally {
      setLoading(false);
    }
  };

  const toggleNotebook = (notebookId: string) => {
    setSelectedNotebooks((prev) =>
      prev.includes(notebookId)
        ? prev.filter((id) => id !== notebookId)
        : [...prev, notebookId]
    );
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              IdeaGen
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Generate creative research ideas, project concepts, and more from your notebooks
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6 space-y-4">
              {/* Notebook Selection */}
              {notebooks.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    <BookOpen className="inline h-4 w-4 mr-1" />
                    Select Notebooks (Optional)
                  </label>
                  <div className="space-y-2 max-h-40 overflow-y-auto border border-zinc-200 dark:border-zinc-700 rounded-md p-3">
                    {notebooks.map((notebook) => (
                      <label
                        key={notebook.id}
                        className="flex items-center cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 p-2 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={selectedNotebooks.includes(notebook.id)}
                          onChange={() => toggleNotebook(notebook.id)}
                          className="mr-2 w-4 h-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-zinc-700 dark:text-zinc-300">
                          {notebook.name} ({notebook.item_count} items)
                        </span>
                      </label>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                    Ideas will be generated based on content from selected notebooks
                  </p>
                </div>
              )}

              {/* Domain Input */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Domain/Topic (Optional)
                </label>
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  placeholder="e.g., Machine Learning, Biology, History..."
                  disabled={loading}
                />
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                  {selectedNotebooks.length > 0
                    ? 'Focus ideas on this domain (optional)'
                    : 'Enter a domain to generate ideas about'}
                </p>
              </div>

              {/* Idea Type */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Idea Type
                </label>
                <select
                  value={ideaType}
                  onChange={(e) => setIdeaType(e.target.value)}
                  className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  disabled={loading}
                >
                  <option value="research">Research Ideas</option>
                  <option value="project">Project Ideas</option>
                  <option value="essay">Essay Topics</option>
                  <option value="presentation">Presentation Topics</option>
                </select>
              </div>

              {/* Count */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  Number of Ideas: {count}
                </label>
                <input
                  type="range"
                  min="3"
                  max="10"
                  value={count}
                  onChange={(e) => setCount(parseInt(e.target.value))}
                  className="w-full"
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading || (!selectedNotebooks.length && !domain.trim())}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating Ideas...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 mr-2" />
                    Generate Ideas
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

          {ideas.length > 0 && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <Lightbulb className="h-5 w-5 mr-2 text-yellow-600" />
                <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  Generated Ideas ({ideas.length})
                </h2>
              </div>
              
              <div className="space-y-4">
                {ideas.map((idea, idx) => (
                  <div
                    key={idx}
                    className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4 border border-zinc-200 dark:border-zinc-700"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                        {idea.title || `Idea ${idx + 1}`}
                      </h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          idea.difficulty === 'easy'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                            : idea.difficulty === 'hard'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                        }`}
                      >
                        {idea.difficulty || 'medium'}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-3">
                      {idea.description}
                    </p>
                    {idea.key_concepts && idea.key_concepts.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {idea.key_concepts.map((concept, cIdx) => (
                          <span
                            key={cIdx}
                            className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
                          >
                            {concept}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
