'use client';

import { ChevronDown, ChevronRight, BookOpen, Loader2, CheckSquare, Square } from 'lucide-react';

interface Notebook {
  id: string;
  name: string;
  icon: string;
  item_count: number;
}

interface NotebookItem {
  id: string;
  type: string;
  title: string;
  content: any;
  created_at: string;
}

interface NotebookSelectorProps {
  notebooks: Notebook[];
  expandedNotebooks: Set<string>;
  notebookRecordsMap: Record<string, NotebookItem[]>;
  selectedRecords: Set<string>;
  loadingNotebooks: boolean;
  loadingRecordsFor: Set<string>;
  isLoading: boolean;
  onToggleExpanded: (notebookId: string) => void;
  onToggleRecord: (notebookId: string, itemId: string) => void;
  onSelectAll: (notebookId: string) => void;
  onDeselectAll: (notebookId: string) => void;
  onClearAll: () => void;
  onCreateSession: () => void;
}

export function NotebookSelector({
  notebooks,
  expandedNotebooks,
  notebookRecordsMap,
  selectedRecords,
  loadingNotebooks,
  loadingRecordsFor,
  isLoading,
  onToggleExpanded,
  onToggleRecord,
  onSelectAll,
  onDeselectAll,
  onClearAll,
  onCreateSession,
}: NotebookSelectorProps) {
  const isRecordSelected = (notebookId: string, itemId: string) => {
    return selectedRecords.has(`${notebookId}:${itemId}`);
  };

  const getNotebookSelectionCount = (notebookId: string) => {
    const items = notebookRecordsMap[notebookId] || [];
    return items.filter(item => isRecordSelected(notebookId, item.id)).length;
  };

  const isNotebookFullySelected = (notebookId: string) => {
    const items = notebookRecordsMap[notebookId] || [];
    if (items.length === 0) return false;
    return items.every(item => isRecordSelected(notebookId, item.id));
  };

  if (loadingNotebooks) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
          <span className="ml-2 text-sm text-slate-500">Loading notebooks...</span>
        </div>
      </div>
    );
  }

  if (notebooks.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <div className="text-center py-8">
          <BookOpen className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No notebooks with items found. Create notebooks and add items first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Select Notebook Items
        </h2>
        {selectedRecords.size > 0 && (
          <button
            onClick={onClearAll}
            className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {notebooks.map(notebook => {
          const isExpanded = expandedNotebooks.has(notebook.id);
          const items = notebookRecordsMap[notebook.id] || [];
          const selectedCount = getNotebookSelectionCount(notebook.id);
          const isFullySelected = isNotebookFullySelected(notebook.id);
          const isLoadingItems = loadingRecordsFor.has(notebook.id);

          return (
            <div
              key={notebook.id}
              className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
            >
              {/* Notebook Header */}
              <div
                className="flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer"
                onClick={() => onToggleExpanded(notebook.id)}
              >
                <div className="flex items-center gap-2 flex-1">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  )}
                  <span className="text-lg">{notebook.icon}</span>
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {notebook.name}
                  </span>
                  <span className="text-xs text-slate-500">
                    ({notebook.item_count} items)
                  </span>
                  {selectedCount > 0 && (
                    <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                      {selectedCount} selected
                    </span>
                  )}
                </div>
                {isExpanded && items.length > 0 && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (isFullySelected) {
                          onDeselectAll(notebook.id);
                        } else {
                          onSelectAll(notebook.id);
                        }
                      }}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {isFullySelected ? 'Deselect All' : 'Select All'}
                    </button>
                  </div>
                )}
              </div>

              {/* Notebook Items */}
              {isExpanded && (
                <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                  {isLoadingItems ? (
                    <div className="p-4 flex items-center justify-center">
                      <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
                      <span className="ml-2 text-xs text-slate-500">Loading items...</span>
                    </div>
                  ) : items.length === 0 ? (
                    <div className="p-4 text-xs text-slate-500 text-center">
                      No items in this notebook
                    </div>
                  ) : (
                    <div className="p-2 space-y-1">
                      {items.map(item => {
                        const recordKey = `${notebook.id}:${item.id}`;
                        const isSelected = isRecordSelected(notebook.id, item.id);
                        
                        return (
                          <div
                            key={item.id}
                            className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
                            onClick={() => onToggleRecord(notebook.id, item.id)}
                          >
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            ) : (
                              <Square className="w-4 h-4 text-slate-400" />
                            )}
                            <span className="text-xs text-slate-700 dark:text-slate-300 flex-1">
                              {item.title}
                            </span>
                            <span className="text-xs text-slate-500 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">
                              {item.type}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Create Session Button */}
      <button
        onClick={onCreateSession}
        disabled={selectedRecords.size === 0 || isLoading}
        className="mt-4 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            Creating Session...
          </span>
        ) : (
          `Create Learning Session (${selectedRecords.size} items selected)`
        )}
      </button>
    </div>
  );
}

