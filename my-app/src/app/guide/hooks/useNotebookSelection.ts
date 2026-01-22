import { useState, useCallback } from 'react';
import { api } from '@/lib/api';

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

interface NotebookRecord {
  notebook_id: string;
  item_id: string;
  notebook_name: string;
  item_title: string;
  item_type: string;
}

export function useNotebookSelection() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [expandedNotebooks, setExpandedNotebooks] = useState<Set<string>>(new Set());
  const [notebookRecordsMap, setNotebookRecordsMap] = useState<Record<string, NotebookItem[]>>({});
  const [selectedRecords, setSelectedRecords] = useState<Set<string>>(new Set());
  const [loadingNotebooks, setLoadingNotebooks] = useState(true);
  const [loadingRecordsFor, setLoadingRecordsFor] = useState<Set<string>>(new Set());

  const fetchNotebooks = useCallback(async () => {
    setLoadingNotebooks(true);
    try {
      const response = await api.notebook.list();
      const nbs = (response.data.notebooks || []).filter((nb: Notebook) => nb.item_count > 0);
      setNotebooks(nbs);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    } finally {
      setLoadingNotebooks(false);
    }
  }, []);

  const fetchRecordsForNotebook = useCallback(async (notebookId: string) => {
    if (notebookRecordsMap[notebookId]) {
      return; // Already loaded
    }

    setLoadingRecordsFor(prev => new Set(prev).add(notebookId));
    try {
      const response = await api.notebook.get(notebookId);
      const items = response.data.items || [];
      setNotebookRecordsMap(prev => ({
        ...prev,
        [notebookId]: items
      }));
    } catch (error) {
      console.error(`Failed to load records for notebook ${notebookId}:`, error);
    } finally {
      setLoadingRecordsFor(prev => {
        const next = new Set(prev);
        next.delete(notebookId);
        return next;
      });
    }
  }, [notebookRecordsMap]);

  const toggleNotebookExpanded = useCallback((notebookId: string) => {
    setExpandedNotebooks(prev => {
      const next = new Set(prev);
      if (next.has(notebookId)) {
        next.delete(notebookId);
      } else {
        next.add(notebookId);
        fetchRecordsForNotebook(notebookId);
      }
      return next;
    });
  }, [fetchRecordsForNotebook]);

  const toggleRecordSelection = useCallback((notebookId: string, itemId: string) => {
    const recordKey = `${notebookId}:${itemId}`;
    setSelectedRecords(prev => {
      const next = new Set(prev);
      if (next.has(recordKey)) {
        next.delete(recordKey);
      } else {
        next.add(recordKey);
      }
      return next;
    });
  }, []);

  const selectAllFromNotebook = useCallback((notebookId: string) => {
    const items = notebookRecordsMap[notebookId] || [];
    setSelectedRecords(prev => {
      const next = new Set(prev);
      items.forEach(item => {
        next.add(`${notebookId}:${item.id}`);
      });
      return next;
    });
  }, [notebookRecordsMap]);

  const deselectAllFromNotebook = useCallback((notebookId: string) => {
    const items = notebookRecordsMap[notebookId] || [];
    setSelectedRecords(prev => {
      const next = new Set(prev);
      items.forEach(item => {
        next.delete(`${notebookId}:${item.id}`);
      });
      return next;
    });
  }, [notebookRecordsMap]);

  const clearAllSelections = useCallback(() => {
    setSelectedRecords(new Set());
  }, []);

  // Convert selected records to format needed for API
  const getSelectedNotebookIds = useCallback((): string[] => {
    const notebookIds = new Set<string>();
    selectedRecords.forEach(recordKey => {
      const [notebookId] = recordKey.split(':');
      notebookIds.add(notebookId);
    });
    return Array.from(notebookIds);
  }, [selectedRecords]);

  return {
    notebooks,
    expandedNotebooks,
    notebookRecordsMap,
    selectedRecords,
    loadingNotebooks,
    loadingRecordsFor,
    fetchNotebooks,
    toggleNotebookExpanded,
    toggleRecordSelection,
    selectAllFromNotebook,
    deselectAllFromNotebook,
    clearAllSelections,
    getSelectedNotebookIds,
  };
}

