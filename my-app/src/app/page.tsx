'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  BookOpen,
  FileText,
  Notebook,
  Activity,
  TrendingUp,
  Target,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DashboardStats {
  knowledge_bases: {
    total: number;
    total_documents: number;
  };
  notebooks: {
    total: number;
    total_items: number;
  };
  guide_sessions: {
    total: number;
    completed: number;
    active: number;
  };
  recent_activities: any[];
  activity_over_time: Array<{
    date: string;
    notebook_items: number;
    guide_sessions: number;
    notebooks: number;
  }>;
  system_status: {
    llm_connected: boolean;
    vector_db_ready: boolean;
  };
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await api.dashboard.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Your AI-powered learning assistant
          </p>
        </div>

        {/* Stats Cards */}
        {!loading && stats && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BookOpen className="h-6 w-6 text-blue-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-zinc-500 dark:text-zinc-400 truncate">
                        Knowledge Bases
                      </dt>
                      <dd className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                        {stats.knowledge_bases.total}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-zinc-500 dark:text-zinc-400 truncate">
                        Documents
                      </dt>
                      <dd className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                        {stats.knowledge_bases.total_documents}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Notebook className="h-6 w-6 text-yellow-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-zinc-500 dark:text-zinc-400 truncate">
                        Notebooks
                      </dt>
                      <dd className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                        {stats.notebooks.total}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Activity className="h-6 w-6 text-purple-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-zinc-500 dark:text-zinc-400 truncate">
                        System Status
                      </dt>
                      <dd className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                        {stats.system_status.llm_connected ? 'Ready' : 'Offline'}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Progress Charts */}
        {!loading && stats && stats.activity_over_time && stats.activity_over_time.length > 0 && (
          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Activity Over Time Chart */}
            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <TrendingUp className="h-5 w-5 text-blue-400 mr-2" />
                  <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                    Activity Over Time
                  </h2>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.activity_over_time}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fill: '#71717a', fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getMonth() + 1}/${date.getDate()}`;
                    }}
                  />
                  <YAxis tick={{ fill: '#71717a', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#18181b', 
                      border: '1px solid #27272a',
                      borderRadius: '8px'
                    }}
                    labelFormatter={(value) => {
                      const date = new Date(value);
                      return date.toLocaleDateString();
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="notebook_items" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    name="Notebook Items"
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="guide_sessions" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Guide Sessions"
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="notebooks" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    name="Notebooks Created"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Learning Progress Chart */}
            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <Target className="h-5 w-5 text-green-400 mr-2" />
                  <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                    Learning Progress
                  </h2>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  {
                    name: 'Notebooks',
                    value: stats.notebooks.total,
                  },
                  {
                    name: 'Items',
                    value: stats.notebooks.total_items,
                  },
                  {
                    name: 'Guides',
                    value: stats.guide_sessions.total,
                  },
                  {
                    name: 'Completed',
                    value: stats.guide_sessions.completed,
                  }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fill: '#71717a', fontSize: 12 }}
                  />
                  <YAxis tick={{ fill: '#71717a', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#18181b', 
                      border: '1px solid #27272a',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Guide Sessions Stats */}
        {!loading && stats && stats.guide_sessions && (
          <div className="mt-8">
            <div className="bg-white dark:bg-zinc-900 overflow-hidden shadow rounded-lg p-6">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
                Guide Sessions Overview
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4">
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">Total Sessions</div>
                  <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mt-1">
                    {stats.guide_sessions.total}
                  </div>
                </div>
                <div className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4">
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">Active</div>
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
                    {stats.guide_sessions.active}
                  </div>
                </div>
                <div className="bg-zinc-50 dark:bg-zinc-800 rounded-lg p-4">
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">Completed</div>
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                    {stats.guide_sessions.completed}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
