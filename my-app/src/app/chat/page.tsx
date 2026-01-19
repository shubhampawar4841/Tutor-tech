'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { MessageSquare, Send, BookOpen, Brain } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: any[];
}

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKB, setSelectedKB] = useState<string>('');
  const [useRAG, setUseRAG] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    createSession();
    loadKnowledgeBases();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadKnowledgeBases = async () => {
    try {
      const response = await api.knowledgeBase.list();
      const kbs = response.data.knowledge_bases || [];
      setKnowledgeBases(kbs);
      // Auto-select first KB if available
      if (kbs.length > 0 && !selectedKB) {
        setSelectedKB(kbs[0].id);
        setUseRAG(true); // Auto-enable RAG if KB available
      }
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const createSession = async () => {
    try {
      const response = await api.chat.createSession();
      setSessionId(response.data.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await api.chat.sendMessage(sessionId, {
        message: currentInput,
        knowledge_base_id: useRAG && selectedKB ? selectedKB : undefined,
        use_rag: useRAG && selectedKB ? true : false,
        use_web_search: false,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response || 'No response',
        timestamp: new Date().toISOString(),
        citations: response.data.citations,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-6 flex flex-col h-full">
      <div className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 md:px-8 flex flex-col">
        <div className="px-4 sm:px-0 mb-4">
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            Chat
          </h1>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Ask questions and get instant answers {useRAG && selectedKB && 'with knowledge base context'}
          </p>
        </div>

        {/* Knowledge Base Selector */}
        {knowledgeBases.length > 0 && (
          <div className="mb-4 bg-white dark:bg-zinc-900 rounded-lg shadow p-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                  <BookOpen className="inline h-4 w-4 mr-1" />
                  Knowledge Base (Optional)
                </label>
                <select
                  value={selectedKB}
                  onChange={(e) => {
                    setSelectedKB(e.target.value);
                    if (!e.target.value) setUseRAG(false);
                  }}
                  className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  disabled={loading}
                >
                  <option value="">None (General Chat)</option>
                  {knowledgeBases.map((kb) => (
                    <option key={kb.id} value={kb.id}>
                      {kb.name} ({kb.document_count} documents)
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center pt-6">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRAG && !!selectedKB}
                    onChange={(e) => setUseRAG(e.target.checked && !!selectedKB)}
                    disabled={!selectedKB || loading}
                    className="mr-2 w-4 h-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-zinc-700 dark:text-zinc-300 flex items-center">
                    <Brain className="h-4 w-4 mr-1" />
                    Use RAG
                  </span>
                </label>
              </div>
            </div>
            {useRAG && selectedKB && (
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                ✓ Chat will use your knowledge base for context-aware responses
              </p>
            )}
          </div>
        )}

        <div className="flex-1 bg-white dark:bg-zinc-900 rounded-lg shadow flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-zinc-500 dark:text-zinc-400 py-12">
                <MessageSquare className="mx-auto h-12 w-12 mb-4" />
                <p>Start a conversation by typing a message below</p>
                {useRAG && selectedKB && (
                  <p className="mt-2 text-sm">Using knowledge base: {knowledgeBases.find(kb => kb.id === selectedKB)?.name}</p>
                )}
              </div>
            ) : (
              messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div className="max-w-xs lg:max-w-md">
                    <div
                      className={`px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                        <span className="font-medium">Sources:</span> {message.citations.length} citation(s)
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-zinc-100 dark:bg-zinc-800 px-4 py-2 rounded-lg">
                  <p className="text-zinc-500 dark:text-zinc-400">
                    {useRAG && selectedKB ? 'Searching knowledge base...' : 'Thinking...'}
                  </p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="border-t border-zinc-200 dark:border-zinc-700 p-4">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="flex-1 px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                placeholder={useRAG && selectedKB ? "Ask about your knowledge base..." : "Type your message..."}
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}


