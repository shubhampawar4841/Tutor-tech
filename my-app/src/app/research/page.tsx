'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { WebSocketClient, getWebSocketUrl } from '@/lib/websocket';
import { Search, Send, Loader2, FileText } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function ResearchPage() {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [researchId, setResearchId] = useState<string | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const wsRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setProgress(null);
    setResult(null);

    try {
      const response = await api.research.start({
        topic: topic,
        mode: 'auto',
        max_subtopics: 5,
        execution_mode: 'series',
      });
      
      setResearchId(response.data.research_id);
      
      // Connect WebSocket for real-time updates
      const ws = new WebSocketClient(
        getWebSocketUrl(`/api/v1/research/${response.data.research_id}/stream`)
      );
      
      ws.on('writing_section', (data) => {
        setProgress(data);
      });
      
      ws.on('completed', (data) => {
        setLoading(false);
        loadResult(response.data.research_id);
      });
      
      ws.connect();
      wsRef.current = ws;
      
    } catch (error) {
      console.error('Failed to start research:', error);
      setLoading(false);
    }
  };

  const loadResult = async (id: string) => {
    try {
      const response = await api.research.getResult(id);
      setResult(response.data);
    } catch (error) {
      console.error('Failed to load result:', error);
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              Deep Research
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Generate comprehensive research reports on any topic
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mb-6">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Research Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-4 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                placeholder="Enter research topic..."
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !topic.trim()}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Researching...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Start Research
                  </>
                )}
              </button>
            </div>
          </form>

          {progress && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6 mb-6">
              <div className="flex items-center mb-4">
                <Search className="h-5 w-5 mr-2 text-blue-600" />
                <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                  {progress.current_section}
                </h3>
              </div>
              {progress.total_sections && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                    <span>
                      Section {progress.section_index + 1} of {progress.total_sections}
                    </span>
                    <span>
                      {Math.round(((progress.section_index + 1) / progress.total_sections) * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{
                        width: `${((progress.section_index + 1) / progress.total_sections) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {result && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center mb-4">
                <FileText className="h-5 w-5 mr-2 text-green-600" />
                <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  Research Complete
                </h2>
              </div>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Report generated successfully. Download or view the report.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


