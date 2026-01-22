'use client';

import { Play, ChevronRight, Loader2 } from 'lucide-react';

interface SessionState {
  status: string;
  current_index: number;
  total_knowledge_points: number;
}

interface ProgressPanelProps {
  sessionState: SessionState;
  isLoading: boolean;
  canStart: boolean;
  canNext: boolean;
  isLastKnowledge: boolean;
  onStartLearning: () => void;
  onNextKnowledge: () => void;
}

export function ProgressPanel({
  sessionState,
  isLoading,
  canStart,
  canNext,
  isLastKnowledge,
  onStartLearning,
  onNextKnowledge,
}: ProgressPanelProps) {
  const progress = sessionState.total_knowledge_points > 0
    ? ((sessionState.current_index + (sessionState.status === 'learning' ? 1 : 0)) / sessionState.total_knowledge_points) * 100
    : 0;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4">
      <div className="mb-3">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-slate-700 dark:text-slate-300 font-medium">
            {sessionState.status === 'learning'
              ? `Knowledge Point ${sessionState.current_index + 1} of ${sessionState.total_knowledge_points}`
              : 'Ready to Start'}
          </span>
          <span className="text-slate-500 dark:text-slate-400">
            {Math.round(progress)}%
          </span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex gap-2">
        {canStart && (
          <button
            onClick={onStartLearning}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Learning
              </>
            )}
          </button>
        )}

        {canNext && (
          <button
            onClick={onNextKnowledge}
            disabled={isLoading || isLastKnowledge}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                Next
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

