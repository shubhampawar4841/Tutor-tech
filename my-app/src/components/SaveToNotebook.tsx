'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { BookOpen, X, Loader2 } from 'lucide-react';

interface Notebook {
  id: string;
  name: string;
  icon: string;
}

interface SaveToNotebookProps {
  itemType: 'solve' | 'question' | 'research' | 'note';
  title: string;
  content: any;
  onSaved?: () => void;
}

export default function SaveToNotebook({ itemType, title, content, onSaved }: SaveToNotebookProps) {
  const [showModal, setShowModal] = useState(false);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [selectedNotebook, setSelectedNotebook] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (showModal) {
      loadNotebooks();
    }
  }, [showModal]);

  const loadNotebooks = async () => {
    setLoading(true);
    try {
      const response = await api.notebook.list();
      setNotebooks(response.data.notebooks || []);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedNotebook) return;

    setSaving(true);
    try {
      await api.notebook.addItem(selectedNotebook, {
        type: itemType,
        title: title,
        content: content,
      });
      setShowModal(false);
      setSelectedNotebook('');
      if (onSaved) {
        onSaved();
      }
      alert('Saved to notebook successfully!');
    } catch (error: any) {
      console.error('Failed to save to notebook:', error);
      alert(error.response?.data?.detail || 'Failed to save to notebook');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800"
      >
        <BookOpen className="h-4 w-4 mr-1.5" />
        Save to Notebook
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                Save to Notebook
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-zinc-400" />
                <p className="mt-2 text-sm text-zinc-500">Loading notebooks...</p>
              </div>
            ) : notebooks.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-zinc-400 mx-auto mb-3" />
                <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
                  No notebooks found. Create one first.
                </p>
                <a
                  href="/notebook"
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Go to Notebooks →
                </a>
              </div>
            ) : (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Select Notebook
                  </label>
                  <select
                    value={selectedNotebook}
                    onChange={(e) => setSelectedNotebook(e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  >
                    <option value="">Choose a notebook...</option>
                    {notebooks.map((notebook) => (
                      <option key={notebook.id} value={notebook.id}>
                        {notebook.icon} {notebook.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={!selectedNotebook || saving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 inline-block mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save'
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}






