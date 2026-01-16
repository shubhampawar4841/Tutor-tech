'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Notebook, Plus, Trash2, X, BookOpen, HelpCircle, Search, FileText, ArrowLeft } from 'lucide-react';

interface NotebookItem {
  id: string;
  name: string;
  description: string;
  color: string;
  icon: string;
  item_count: number;
}

interface NotebookItemDetail {
  id: string;
  notebook_id: string;
  type: string;
  title: string;
  content: any;
  created_at: string;
}

export default function NotebookPage() {
  const [notebooks, setNotebooks] = useState<NotebookItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newNotebookName, setNewNotebookName] = useState('');
  const [selectedNotebook, setSelectedNotebook] = useState<NotebookItem | null>(null);
  const [notebookItems, setNotebookItems] = useState<NotebookItemDetail[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);

  useEffect(() => {
    loadNotebooks();
  }, []);

  const loadNotebooks = async () => {
    try {
      const response = await api.notebook.list();
      setNotebooks(response.data.notebooks || []);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadNotebookItems = async (notebookId: string) => {
    setLoadingItems(true);
    try {
      const response = await api.notebook.get(notebookId);
      setNotebookItems(response.data.items || []);
    } catch (error) {
      console.error('Failed to load notebook items:', error);
    } finally {
      setLoadingItems(false);
    }
  };

  const handleCreate = async () => {
    if (!newNotebookName.trim()) return;
    
    try {
      await api.notebook.create({
        name: newNotebookName.trim(),
        description: '',
        color: '#3b82f6',
        icon: '📓',
      });
      setShowCreateModal(false);
      setNewNotebookName('');
      loadNotebooks();
    } catch (error) {
      console.error('Failed to create notebook:', error);
      alert('Failed to create notebook');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this notebook? All items will be deleted.')) {
      try {
        await api.notebook.delete(id);
        if (selectedNotebook?.id === id) {
          setSelectedNotebook(null);
          setNotebookItems([]);
        }
        loadNotebooks();
      } catch (error) {
        console.error('Failed to delete notebook:', error);
        alert('Failed to delete notebook');
      }
    }
  };

  const handleSelectNotebook = async (notebook: NotebookItem) => {
    setSelectedNotebook(notebook);
    await loadNotebookItems(notebook.id);
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!selectedNotebook) return;
    
    if (confirm('Are you sure you want to delete this item?')) {
      try {
        await api.notebook.deleteItem(selectedNotebook.id, itemId);
        await loadNotebookItems(selectedNotebook.id);
        loadNotebooks(); // Refresh to update item_count
      } catch (error) {
        console.error('Failed to delete item:', error);
        alert('Failed to delete item');
      }
    }
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'solve':
        return <BookOpen className="h-5 w-5" />;
      case 'question':
        return <HelpCircle className="h-5 w-5" />;
      case 'research':
        return <Search className="h-5 w-5" />;
      case 'note':
        return <FileText className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const formatItemContent = (item: NotebookItemDetail) => {
    if (item.type === 'solve') {
      return (
        <div className="text-sm text-zinc-600 dark:text-zinc-400">
          <p className="font-medium mb-1">Question:</p>
          <p className="mb-2">{item.content?.question || 'N/A'}</p>
          {item.content?.answer && (
            <>
              <p className="font-medium mb-1">Answer:</p>
              <p className="whitespace-pre-wrap">{item.content.answer.substring(0, 200)}...</p>
            </>
          )}
        </div>
      );
    } else if (item.type === 'question') {
      return (
        <div className="text-sm text-zinc-600 dark:text-zinc-400">
          <p className="font-medium mb-1">Question:</p>
          <p className="mb-2">{item.content?.question || 'N/A'}</p>
          {item.content?.answer && (
            <>
              <p className="font-medium mb-1">Answer:</p>
              <p>{item.content.answer.substring(0, 200)}...</p>
            </>
          )}
        </div>
      );
    } else if (item.type === 'research') {
      return (
        <div className="text-sm text-zinc-600 dark:text-zinc-400">
          <p className="font-medium mb-1">Topic:</p>
          <p className="mb-2">{item.content?.topic || 'N/A'}</p>
          {item.content?.summary && (
            <>
              <p className="font-medium mb-1">Summary:</p>
              <p>{item.content.summary.substring(0, 200)}...</p>
            </>
          )}
        </div>
      );
    } else {
      return (
        <div className="text-sm text-zinc-600 dark:text-zinc-400">
          <p className="whitespace-pre-wrap">{item.content?.text || item.content || 'No content'}</p>
        </div>
      );
    }
  };

  if (selectedNotebook) {
    return (
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
          <div className="px-4 sm:px-0">
            <button
              onClick={() => {
                setSelectedNotebook(null);
                setNotebookItems([]);
              }}
              className="mb-4 inline-flex items-center text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-50"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Notebooks
            </button>

            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">{selectedNotebook.icon}</span>
                <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                  {selectedNotebook.name}
                </h1>
              </div>
              {selectedNotebook.description && (
                <p className="text-sm text-zinc-600 dark:text-zinc-400 ml-11">
                  {selectedNotebook.description}
                </p>
              )}
              <p className="text-sm text-zinc-500 dark:text-zinc-500 ml-11 mt-1">
                {notebookItems.length} {notebookItems.length === 1 ? 'item' : 'items'}
              </p>
            </div>

            {loadingItems ? (
              <div className="text-center py-12">Loading items...</div>
            ) : notebookItems.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-zinc-900 rounded-lg shadow">
                <FileText className="mx-auto h-12 w-12 text-zinc-400 mb-4" />
                <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-50 mb-2">
                  No items yet
                </h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  Items saved from other features will appear here.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {notebookItems.map((item) => (
                  <div
                    key={item.id}
                    className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-zinc-400 dark:text-zinc-500 mt-0.5">
                          {getItemIcon(item.type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                              {item.title}
                            </h3>
                            <span className="text-xs px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded text-zinc-600 dark:text-zinc-400">
                              {item.type}
                            </span>
                          </div>
                          {formatItemContent(item)}
                          <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-3">
                            {new Date(item.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="ml-4 text-zinc-400 hover:text-red-600 dark:hover:text-red-400"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                Notebook
              </h1>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                Organize your learning materials
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Notebook
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12">Loading...</div>
          ) : notebooks.length === 0 ? (
            <div className="text-center py-12">
              <Notebook className="mx-auto h-12 w-12 text-zinc-400" />
              <h3 className="mt-2 text-sm font-medium text-zinc-900 dark:text-zinc-50">
                No notebooks
              </h3>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                Get started by creating a new notebook.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {notebooks.map((notebook) => (
                <div
                  key={notebook.id}
                  onClick={() => handleSelectNotebook(notebook)}
                  className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-2xl mr-2">{notebook.icon}</span>
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                          {notebook.name}
                        </h3>
                      </div>
                      <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
                        {notebook.description || 'No description'}
                      </p>
                      <div className="text-sm text-zinc-500 dark:text-zinc-400">
                        {notebook.item_count} {notebook.item_count === 1 ? 'item' : 'items'}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(notebook.id);
                      }}
                      className="ml-4 text-zinc-400 hover:text-red-600 dark:hover:text-red-400"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                  Create Notebook
                </h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={newNotebookName}
                    onChange={(e) => setNewNotebookName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCreate();
                      }
                    }}
                    className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                    placeholder="My Notebook"
                    autoFocus
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newNotebookName.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
