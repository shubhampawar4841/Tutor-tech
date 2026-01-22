'use client';

import { useState } from 'react';
import { Send, Loader2, CheckCircle2, XCircle, HelpCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface Question {
  question: string;
  type: string;
  hint?: string;
  expected_key_points?: string[];
  answer?: string;
  options?: string[];
  difficulty?: string;
}

interface QuestionsPanelProps {
  questions: Question[];
  knowledgePointNumber: number;
  sessionId: string;
  onAnswerSubmitted?: (score: number, needsReview: boolean) => void;
}

export function QuestionsPanel({
  questions,
  knowledgePointNumber,
  sessionId,
  onAnswerSubmitted,
}: QuestionsPanelProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [textAnswers, setTextAnswers] = useState<Record<number, string>>({});
  const [submitting, setSubmitting] = useState<Record<number, boolean>>({});
  const [evaluations, setEvaluations] = useState<Record<number, any>>({});
  const [showHints, setShowHints] = useState<Record<number, boolean>>({});

  if (!questions || questions.length === 0) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mt-4">
        <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm">
            No questions available for this knowledge point. Generate questions in the Questions section and save them to notebooks.
          </p>
        </div>
      </div>
    );
  }

  const handleSubmitAnswer = async (questionIndex: number, question: Question) => {
    const answer = question.type === 'multiple_choice' 
      ? selectedAnswers[questionIndex] 
      : textAnswers[questionIndex];

    if (!answer || !answer.trim()) {
      alert('Please provide an answer');
      return;
    }

    setSubmitting(prev => ({ ...prev, [questionIndex]: true }));

    try {
      const response = await api.guide.submitAnswer(sessionId, {
        step_number: knowledgePointNumber,
        question_index: questionIndex,
        answer: answer,
      });

      const evaluation = response.data.evaluation;
      setEvaluations(prev => ({ ...prev, [questionIndex]: evaluation }));

      if (onAnswerSubmitted) {
        onAnswerSubmitted(
          response.data.understanding_score || evaluation.score || 0,
          response.data.needs_review || false
        );
      }
    } catch (error: any) {
      console.error('Failed to submit answer:', error);
      alert(error.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setSubmitting(prev => ({ ...prev, [questionIndex]: false }));
    }
  };

  return (
    <div className="mt-6 space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
        <HelpCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        Practice Questions
      </h2>

      {questions.map((q, idx) => {
        const evaluation = evaluations[idx];
        const isEvaluated = !!evaluation;
        const isCorrect = evaluation?.is_correct || false;
        const score = evaluation?.score || 0;

        return (
          <div
            key={idx}
            className={`border rounded-lg p-5 ${
              isEvaluated
                ? isCorrect
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                  : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    Question {idx + 1}
                  </span>
                  {q.difficulty && (
                    <span className="text-xs px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-400">
                      {q.difficulty}
                    </span>
                  )}
                  {isEvaluated && (
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        isCorrect
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                      }`}
                    >
                      Score: {Math.round(score * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-slate-900 dark:text-slate-100 font-medium mb-3">
                  {q.question}
                </p>
              </div>
            </div>

            {/* Answer Input */}
            {!isEvaluated && (
              <div className="mb-4">
                {q.type === 'multiple_choice' && q.options && q.options.length > 0 ? (
                  <div className="space-y-2">
                    {q.options.map((option, optIdx) => {
                      const isSelected = selectedAnswers[idx] === option;
                      return (
                        <label
                          key={optIdx}
                          className={`flex items-center gap-2 p-3 rounded cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-300 dark:border-blue-700'
                              : 'bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600'
                          }`}
                        >
                          <input
                            type="radio"
                            name={`question-${idx}`}
                            checked={isSelected}
                            onChange={() =>
                              setSelectedAnswers(prev => ({ ...prev, [idx]: option }))
                            }
                            className="w-4 h-4 text-blue-600"
                          />
                          <span className="font-medium text-slate-600 dark:text-slate-400 w-6">
                            {String.fromCharCode(65 + optIdx)}.
                          </span>
                          <span className="flex-1 text-slate-700 dark:text-slate-300">
                            {option}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <textarea
                    value={textAnswers[idx] || ''}
                    onChange={(e) =>
                      setTextAnswers(prev => ({ ...prev, [idx]: e.target.value }))
                    }
                    placeholder="Type your answer here..."
                    className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 min-h-[100px]"
                    disabled={submitting[idx]}
                  />
                )}

                {/* Hint */}
                {q.hint && (
                  <div className="mt-3">
                    <button
                      onClick={() =>
                        setShowHints(prev => ({ ...prev, [idx]: !prev[idx] }))
                      }
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {showHints[idx] ? 'Hide Hint' : 'Show Hint'}
                    </button>
                    {showHints[idx] && (
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 italic">
                        {q.hint}
                      </p>
                    )}
                  </div>
                )}

                {/* Submit Button */}
                <button
                  onClick={() => handleSubmitAnswer(idx, q)}
                  disabled={
                    submitting[idx] ||
                    (!selectedAnswers[idx] && !textAnswers[idx]?.trim())
                  }
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
                >
                  {submitting[idx] ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Evaluating...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Submit Answer
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Evaluation Feedback */}
            {isEvaluated && evaluation && (
              <div
                className={`mt-4 p-4 rounded-lg border ${
                  isCorrect
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                    : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}
              >
                <div className="flex items-start gap-2 mb-2">
                  {isCorrect ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <p
                      className={`text-sm font-medium mb-1 ${
                        isCorrect
                          ? 'text-green-900 dark:text-green-100'
                          : 'text-red-900 dark:text-red-100'
                      }`}
                    >
                      {isCorrect ? 'Correct!' : 'Needs Improvement'}
                    </p>
                    <p
                      className={`text-sm ${
                        isCorrect
                          ? 'text-green-800 dark:text-green-200'
                          : 'text-red-800 dark:text-red-200'
                      }`}
                    >
                      {evaluation.feedback}
                    </p>

                    {evaluation.strengths && evaluation.strengths.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-green-900 dark:text-green-100 mb-1">
                          Strengths:
                        </p>
                        <ul className="text-xs text-green-800 dark:text-green-200 list-disc list-inside">
                          {evaluation.strengths.map((strength: string, i: number) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {evaluation.areas_for_improvement &&
                      evaluation.areas_for_improvement.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-red-900 dark:text-red-100 mb-1">
                            Areas for Improvement:
                          </p>
                          <ul className="text-xs text-red-800 dark:text-red-200 list-disc list-inside">
                            {evaluation.areas_for_improvement.map(
                              (area: string, i: number) => (
                                <li key={i}>{area}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}

                    {evaluation.suggestions && evaluation.suggestions.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-slate-900 dark:text-slate-100 mb-1">
                          Suggestions:
                        </p>
                        <ul className="text-xs text-slate-700 dark:text-slate-300 list-disc list-inside">
                          {evaluation.suggestions.map((suggestion: string, i: number) => (
                            <li key={i}>{suggestion}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Show Correct Answer */}
            {isEvaluated && q.answer && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                      Correct Answer:
                    </p>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{q.answer}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

