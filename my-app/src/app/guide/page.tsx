'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { GraduationCap, BookOpen, Loader2, Play, ChevronRight, CheckCircle2, Circle } from 'lucide-react';

interface Notebook {
  id: string;
  name: string;
  icon: string;
  item_count: number;
}

interface GuideStep {
  step_number: number;
  title: string;
  description: string;
  key_points: string[];
  content: string;
  related_items?: string[];
}

interface GuideContent {
  title: string;
  description: string;
  total_steps: number;
  steps: GuideStep[];
}

interface GuideSession {
  session_id: string;
  status: string;
  current_step: number;
  total_steps: number;
  content: GuideContent;
  notebook_ids: string[];
}

export default function GuidePage() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [selectedNotebooks, setSelectedNotebooks] = useState<string[]>([]);
  const [maxPoints, setMaxPoints] = useState(5);
  const [loading, setLoading] = useState(false);
  const [loadingNotebooks, setLoadingNotebooks] = useState(true);
  const [guideSession, setGuideSession] = useState<GuideSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotebooks();
  }, []);

  const loadNotebooks = async () => {
    try {
      const response = await api.notebook.list();
      const nbs = response.data.notebooks || [];
      setNotebooks(nbs.filter((nb: Notebook) => nb.item_count > 0)); // Only show notebooks with items
    } catch (error) {
      console.error('Failed to load notebooks:', error);
    } finally {
      setLoadingNotebooks(false);
    }
  };

  const handleStartGuide = async () => {
    if (selectedNotebooks.length === 0) {
      setError('Please select at least one notebook');
      return;
    }

    setLoading(true);
    setError(null);
    setGuideSession(null);

    try {
      const response = await api.guide.start({
        notebook_ids: selectedNotebooks,
        max_points: maxPoints,
      });

      if (response.data) {
        setGuideSession({
          session_id: response.data.session_id,
          status: response.data.status,
          current_step: response.data.current_step || 1,
          total_steps: response.data.total_steps || 5,
          content: response.data.content,
          notebook_ids: response.data.notebook_ids,
        });
      }
    } catch (error: any) {
      console.error('Failed to start guide:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to start guide');
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = async () => {
    if (!guideSession) return;

    try {
      const response = await api.guide.next(guideSession.session_id);
      if (response.data) {
        setGuideSession({
          ...guideSession,
          current_step: response.data.current_step,
          status: response.data.completed ? 'completed' : 'active',
        });
      }
    } catch (error: any) {
      console.error('Failed to move to next step:', error);
      setError(error.response?.data?.detail || 'Failed to move to next step');
    }
  };

  const toggleNotebook = (notebookId: string) => {
    setSelectedNotebooks((prev) =>
      prev.includes(notebookId)
        ? prev.filter((id) => id !== notebookId)
        : [...prev, notebookId]
    );
  };

  const currentStepData = guideSession?.content?.steps?.find(
    (step) => step.step_number === guideSession.current_step
  );

  if (guideSession && currentStepData) {
    return (
      <div className="py-6">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
          <div className="px-4 sm:px-0">
            <button
              onClick={() => setGuideSession(null)}
              className="mb-4 text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-50"
            >
              ← Back to Start
            </button>

            <div className="mb-6">
              <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                {guideSession.content.title || 'Learning Guide'}
              </h1>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                {guideSession.content.description || 'Interactive learning guide'}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="mb-6 bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Step {guideSession.current_step} of {guideSession.total_steps}
                </span>
                <span className="text-sm text-zinc-500 dark:text-zinc-400">
                  {Math.round((guideSession.current_step / guideSession.total_steps) * 100)}% Complete
                </span>
              </div>
              <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(guideSession.current_step / guideSession.total_steps) * 100}%` }}
                />
              </div>
            </div>

            {/* Current Step */}
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-bold">
                  {guideSession.current_step}
                </div>
                <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                  {currentStepData.title}
                </h2>
              </div>

              <p className="text-zinc-600 dark:text-zinc-400 mb-4">
                {currentStepData.description}
              </p>

              {currentStepData.key_points && currentStepData.key_points.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                    Key Points:
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                    {currentStepData.key_points.map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-zinc-700 dark:text-zinc-300 leading-relaxed">
                  {currentStepData.content}
                </div>
              </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center">
              <div className="text-sm text-zinc-500 dark:text-zinc-400">
                {guideSession.current_step > 1 && (
                  <button
                    onClick={() => {
                      // Go to previous step (would need API endpoint for this)
                      setGuideSession({
                        ...guideSession,
                        current_step: guideSession.current_step - 1,
                      });
                    }}
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    ← Previous Step
                  </button>
                )}
              </div>

              {guideSession.status === 'completed' ? (
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">Guide Completed!</span>
                </div>
              ) : (
                <button
                  onClick={handleNextStep}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  {guideSession.current_step < guideSession.total_steps ? (
                    <>
                      Next Step
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </>
                  ) : (
                    <>
                      Complete Guide
                      <CheckCircle2 className="h-4 w-4 ml-2" />
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Step List */}
            <div className="mt-8 bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
                All Steps
              </h3>
              <div className="space-y-2">
                {guideSession.content.steps.map((step) => (
                  <div
                    key={step.step_number}
                    onClick={() => {
                      setGuideSession({
                        ...guideSession,
                        current_step: step.step_number,
                      });
                    }}
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      step.step_number === guideSession.current_step
                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                        : 'hover:bg-zinc-50 dark:hover:bg-zinc-800'
                    }`}
                  >
                    {step.step_number < guideSession.current_step ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                    ) : step.step_number === guideSession.current_step ? (
                      <Circle className="h-5 w-5 text-blue-600 dark:text-blue-400 fill-current flex-shrink-0" />
                    ) : (
                      <Circle className="h-5 w-5 text-zinc-300 dark:text-zinc-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                        Step {step.step_number}: {step.title}
                      </div>
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">
                        {step.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              Guided Learning
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Create interactive learning guides from your notebooks
            </p>
          </div>

          {error && (
            <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg shadow p-4 mb-6">
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
              Create Learning Guide
            </h2>

            {loadingNotebooks ? (
              <div className="text-center py-8">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-zinc-400" />
                <p className="mt-2 text-sm text-zinc-500">Loading notebooks...</p>
              </div>
            ) : notebooks.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-zinc-400 mx-auto mb-3" />
                <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
                  No notebooks with items found. Add items to notebooks first.
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
                    Select Notebooks
                  </label>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {notebooks.map((notebook) => (
                      <label
                        key={notebook.id}
                        className="flex items-center gap-3 p-3 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedNotebooks.includes(notebook.id)}
                          onChange={() => toggleNotebook(notebook.id)}
                          className="rounded border-zinc-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-2xl">{notebook.icon}</span>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                            {notebook.name}
                          </div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            {notebook.item_count} {notebook.item_count === 1 ? 'item' : 'items'}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Number of Learning Points
                  </label>
                  <input
                    type="number"
                    value={maxPoints}
                    onChange={(e) => setMaxPoints(parseInt(e.target.value) || 5)}
                    min={3}
                    max={10}
                    className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                  />
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    Number of steps in your learning guide (3-10)
                  </p>
                </div>

                <button
                  onClick={handleStartGuide}
                  disabled={loading || selectedNotebooks.length === 0}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Generating Guide...
                    </>
                  ) : (
                    <>
                      <Play className="h-5 w-5 mr-2" />
                      Start Learning Guide
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
