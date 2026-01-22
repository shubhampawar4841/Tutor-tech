'use client';

import { X, CheckCircle2, Clock, Zap, Loader2 } from 'lucide-react';

interface PlanStep {
  step_number: number;
  name: string;
  description: string;
  estimated_time: string;
  dependencies?: number[];
}

interface Plan {
  overview: string;
  steps: PlanStep[];
  estimated_total_time: string;
  complexity: string;
  resources: string[];
  subtopics?: string[];
}

interface PlanModalProps {
  isOpen: boolean;
  plan: Plan | null;
  loading: boolean;
  onApprove: () => void;
  onCancel: () => void;
  onModify?: () => void;
}

export default function PlanModal({
  isOpen,
  plan,
  loading,
  onApprove,
  onCancel,
  onModify,
}: PlanModalProps) {
  if (!isOpen) return null;

  const getComplexityColor = (complexity: string) => {
    switch (complexity.toLowerCase()) {
      case 'simple':
        return 'text-green-600 dark:text-green-400';
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'complex':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-slate-600 dark:text-slate-400';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Research Plan
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Review the plan before execution
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin mb-4" />
              <p className="text-slate-600 dark:text-slate-400">
                Generating research plan...
              </p>
            </div>
          ) : plan ? (
            <div className="space-y-6">
              {/* Overview */}
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  Overview
                </h3>
                <p className="text-slate-700 dark:text-slate-300">
                  {plan.overview}
                </p>
              </div>

              {/* Plan Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Estimated Time
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                    {plan.estimated_total_time}
                  </p>
                </div>

                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Zap className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Complexity
                    </span>
                  </div>
                  <p
                    className={`text-lg font-semibold ${getComplexityColor(
                      plan.complexity
                    )}`}
                  >
                    {plan.complexity}
                  </p>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Steps
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                    {plan.steps.length}
                  </p>
                </div>
              </div>

              {/* Steps */}
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
                  Execution Steps
                </h3>
                <div className="space-y-3">
                  {plan.steps.map((step, idx) => (
                    <div
                      key={step.step_number}
                      className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900/50"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 dark:bg-blue-500 text-white flex items-center justify-center font-semibold text-sm">
                          {step.step_number}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-1">
                            {step.name}
                          </h4>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                            {step.description}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-500">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {step.estimated_time}
                            </span>
                            {step.dependencies && step.dependencies.length > 0 && (
                              <span>
                                Depends on: Step {step.dependencies.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Subtopics */}
              {plan.subtopics && plan.subtopics.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
                    Subtopics to Research
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {plan.subtopics.map((subtopic, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-full text-sm"
                      >
                        {subtopic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Resources */}
              {plan.resources && plan.resources.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
                    Resources
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {plan.resources.map((resource, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm"
                      >
                        {resource}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-slate-500 dark:text-slate-400">
                No plan available
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
          <div className="flex gap-3">
            {onModify && (
              <button
                onClick={onModify}
                className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Modify
              </button>
            )}
            <button
              onClick={onApprove}
              disabled={!plan || loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              Approve & Start
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

