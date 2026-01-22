'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { HelpCircle, Send, Loader2, BookOpen, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import SaveToNotebook from '@/components/SaveToNotebook';

interface KnowledgeBase {
  id: string;
  name: string;
}

interface Question {
  question: string;
  type: string;
  difficulty: string;
  answer: string;
  options?: string[];
}

interface Evaluation {
  score: number;
  feedback: string;
  is_correct: boolean;
  suggestions?: string[];
  strengths?: string[];
  areas_for_improvement?: string[];
}

interface QuestionState {
  userAnswer: string;
  evaluation: Evaluation | null;
  evaluating: boolean;
  evaluated: boolean;
  savedToNotebook: boolean;
}

export default function QuestionsPage() {
  const [knowledgePoint, setKnowledgePoint] = useState('');
  const [selectedKB, setSelectedKB] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState('medium');
  const [questionType, setQuestionType] = useState('multiple_choice');
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [showAnswers, setShowAnswers] = useState<{ [key: number]: boolean }>({});
  const [questionStates, setQuestionStates] = useState<{ [key: number]: QuestionState }>({});

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    try {
      const response = await api.knowledgeBase.list();
      const kbs = response.data.knowledge_bases || [];
      setKnowledgeBases(kbs);
      // Auto-select first KB if available
      if (kbs.length > 0 && !selectedKB) {
        setSelectedKB(kbs[0].id);
      }
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!knowledgePoint.trim()) {
      setError('Please enter a knowledge point/topic');
      return;
    }
    if (!selectedKB) {
      setError('Please select a knowledge base');
      return;
    }

    setLoading(true);
    setQuestions([]);
    setError(null);
    setShowAnswers({});
    setQuestionStates({});

    try {
      const response = await api.question.generate({
        knowledge_base_id: selectedKB,
        topic: knowledgePoint.trim(),
        difficulty: difficulty,
        question_type: questionType,
        count: count,
      });
      
      if (response.data.success) {
        setQuestions(response.data.questions || []);
      } else {
        setError(response.data.error || 'Failed to generate questions');
      }
    } catch (error: any) {
      console.error('Failed to generate questions:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to generate questions');
    } finally {
      setLoading(false);
    }
  };

  const toggleAnswer = (idx: number) => {
    setShowAnswers(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const handleAnswerChange = (idx: number, answer: string) => {
    setQuestionStates(prev => ({
      ...prev,
      [idx]: {
        ...prev[idx],
        userAnswer: answer,
        evaluated: false,
        evaluation: null,
      }
    }));
  };

  const handleSubmitAnswer = async (idx: number, question: Question) => {
    const state = questionStates[idx];
    if (!state || !state.userAnswer.trim()) {
      setError('Please enter an answer');
      return;
    }

    // Set evaluating state
    setQuestionStates(prev => ({
      ...prev,
      [idx]: {
        ...prev[idx],
        evaluating: true,
      }
    }));

    try {
      const response = await api.question.evaluate({
        question: question,
        user_answer: state.userAnswer,
        knowledge_point: knowledgePoint,
        knowledge_base_id: selectedKB || undefined,
        auto_save_to_notebook: true,
      });

      if (response.data.success) {
        const evaluation = response.data.evaluation;
        setQuestionStates(prev => ({
          ...prev,
          [idx]: {
            ...prev[idx],
            evaluation: evaluation,
            evaluated: true,
            evaluating: false,
            savedToNotebook: response.data.saved_to_notebook || false,
          }
        }));

        if (response.data.saved_to_notebook) {
          // Show success message
          setTimeout(() => {
            alert('Your answer was saved to "Learning Gaps" notebook for review!');
          }, 100);
        }
      }
    } catch (error: any) {
      console.error('Failed to evaluate answer:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to evaluate answer');
      setQuestionStates(prev => ({
        ...prev,
        [idx]: {
          ...prev[idx],
          evaluating: false,
        }
      }));
    }
  };

  return (
    <div className="py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
              Question Generator
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Generate practice questions from your knowledge base using RAG
            </p>
          </div>

          <form onSubmit={handleGenerate} className="mb-6">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="space-y-4">
                <div>
                  <label htmlFor="kb-select" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Knowledge Base
                  </label>
                  <select
                    id="kb-select"
                    value={selectedKB || ''}
                    onChange={(e) => setSelectedKB(e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                    disabled={loading || knowledgeBases.length === 0}
                  >
                    <option value="">
                      {knowledgeBases.length === 0 ? 'No knowledge bases available' : 'Select a knowledge base'}
                    </option>
                    {knowledgeBases.map((kb) => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="knowledge-point" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                    Knowledge Point / Topic
                  </label>
                  <input
                    id="knowledge-point"
                    type="text"
                    value={knowledgePoint}
                    onChange={(e) => setKnowledgePoint(e.target.value)}
                    className="w-full px-4 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                    placeholder="e.g., virtual hospitals, machine learning, photosynthesis..."
                    disabled={loading}
                  />
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    Enter the topic or knowledge point you want questions about
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="difficulty" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Difficulty
                    </label>
                    <select
                      id="difficulty"
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                      disabled={loading}
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="question-type" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Question Type
                    </label>
                    <select
                      id="question-type"
                      value={questionType}
                      onChange={(e) => setQuestionType(e.target.value)}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                      disabled={loading}
                    >
                      <option value="multiple_choice">Multiple Choice</option>
                      <option value="short_answer">Short Answer</option>
                      <option value="true_false">True/False</option>
                      <option value="fill_blank">Fill in the Blank</option>
                      <option value="essay">Essay</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="count" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Number of Questions
                    </label>
                    <input
                      id="count"
                      type="number"
                      value={count}
                      onChange={(e) => setCount(parseInt(e.target.value) || 5)}
                      min={1}
                      max={20}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                      disabled={loading}
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !knowledgePoint.trim() || !selectedKB}
                className="mt-6 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5 mr-2" />
                    Generate Questions
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg shadow p-4 mb-6">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {questions.length > 0 && (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                  Generated Questions ({questions.length})
                </h2>
                <div className="flex items-center gap-3">
                  <div className="text-sm text-zinc-600 dark:text-zinc-400">
                    {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)} • {questionType.replace('_', ' ')}
                  </div>
                  <SaveToNotebook
                    itemType="question"
                    title={`${questions.length} Questions about ${knowledgePoint}`}
                    content={{
                      knowledge_point: knowledgePoint,
                      difficulty: difficulty,
                      question_type: questionType,
                      questions: questions,
                      knowledge_base_id: selectedKB,
                    }}
                  />
                </div>
              </div>
              
              <div className="space-y-6">
                {questions.map((q, idx) => {
                  const state = questionStates[idx] || {
                    userAnswer: '',
                    evaluation: null,
                    evaluating: false,
                    evaluated: false,
                    savedToNotebook: false,
                  };

                  return (
                    <div key={idx} className="border border-zinc-200 dark:border-zinc-700 rounded-lg p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                              Question {idx + 1}
                            </span>
                            <span className="text-xs px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded text-zinc-600 dark:text-zinc-400">
                              {q.difficulty || difficulty}
                            </span>
                            {state.evaluated && state.evaluation && (
                              <span className={`text-xs px-2 py-1 rounded ${
                                state.evaluation.is_correct
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                              }`}>
                                Score: {Math.round(state.evaluation.score * 100)}%
                              </span>
                            )}
                            {state.savedToNotebook && (
                              <span className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded">
                                Saved to Learning Gaps
                              </span>
                            )}
                          </div>
                          <p className="text-zinc-900 dark:text-zinc-50 font-medium mb-3">
                            {q.question}
                          </p>
                        </div>
                      </div>

                      {/* Answer Input Section */}
                      {!state.evaluated && (
                        <div className="mb-4">
                          {q.type === 'multiple_choice' && q.options && q.options.length > 0 ? (
                            <div className="ml-4 mb-4">
                              <ul className="space-y-2">
                                {q.options.map((option, optIdx) => {
                                  const isSelected = state.userAnswer === option;
                                  return (
                                    <li
                                      key={optIdx}
                                      className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                                        isSelected
                                          ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-300 dark:border-blue-700'
                                          : 'bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-700'
                                      }`}
                                      onClick={() => handleAnswerChange(idx, option)}
                                    >
                                      <input
                                        type="radio"
                                        name={`question-${idx}`}
                                        checked={isSelected}
                                        onChange={() => handleAnswerChange(idx, option)}
                                        className="w-4 h-4 text-blue-600"
                                      />
                                      <span className="font-medium text-zinc-600 dark:text-zinc-400 w-6">
                                        {String.fromCharCode(65 + optIdx)}.
                                      </span>
                                      <span className="flex-1 text-zinc-700 dark:text-zinc-300">
                                        {option}
                                      </span>
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          ) : (
                            <textarea
                              value={state.userAnswer}
                              onChange={(e) => handleAnswerChange(idx, e.target.value)}
                              placeholder="Type your answer here..."
                              className="w-full px-4 py-3 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 min-h-[100px]"
                              disabled={state.evaluating}
                            />
                          )}

                          <button
                            onClick={() => handleSubmitAnswer(idx, q)}
                            disabled={!state.userAnswer.trim() || state.evaluating}
                            className="mt-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {state.evaluating ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Evaluating...
                              </>
                            ) : (
                              <>
                                <Send className="h-4 w-4 mr-2" />
                                Submit Answer
                              </>
                            )}
                          </button>
                        </div>
                      )}

                      {/* Evaluation Feedback */}
                      {state.evaluated && state.evaluation && (
                        <div className={`mt-4 p-4 rounded-lg border ${
                          state.evaluation.is_correct
                            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                            : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                        }`}>
                          <div className="flex items-start gap-2 mb-2">
                            {state.evaluation.is_correct ? (
                              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                            )}
                            <div className="flex-1">
                              <p className={`text-sm font-medium mb-1 ${
                                state.evaluation.is_correct
                                  ? 'text-green-900 dark:text-green-100'
                                  : 'text-red-900 dark:text-red-100'
                              }`}>
                                {state.evaluation.is_correct ? 'Correct!' : 'Needs Improvement'}
                              </p>
                              <p className={`text-sm ${
                                state.evaluation.is_correct
                                  ? 'text-green-800 dark:text-green-200'
                                  : 'text-red-800 dark:text-red-200'
                              }`}>
                                {state.evaluation.feedback}
                              </p>

                              {state.evaluation.strengths && state.evaluation.strengths.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-medium text-green-900 dark:text-green-100 mb-1">Strengths:</p>
                                  <ul className="text-xs text-green-800 dark:text-green-200 list-disc list-inside">
                                    {state.evaluation.strengths.map((strength, i) => (
                                      <li key={i}>{strength}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {state.evaluation.areas_for_improvement && state.evaluation.areas_for_improvement.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-medium text-red-900 dark:text-red-100 mb-1">Areas for Improvement:</p>
                                  <ul className="text-xs text-red-800 dark:text-red-200 list-disc list-inside">
                                    {state.evaluation.areas_for_improvement.map((area, i) => (
                                      <li key={i}>{area}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {state.evaluation.suggestions && state.evaluation.suggestions.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100 mb-1">Suggestions:</p>
                                  <ul className="text-xs text-zinc-700 dark:text-zinc-300 list-disc list-inside">
                                    {state.evaluation.suggestions.map((suggestion, i) => (
                                      <li key={i}>{suggestion}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Show Correct Answer (after evaluation) */}
                      {state.evaluated && (
                        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                          <div className="flex items-start gap-2">
                            <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                                Correct Answer:
                              </p>
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                {q.answer}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Show Answer Button (if not evaluated yet) */}
                      {!state.evaluated && (
                        <button
                          onClick={() => toggleAnswer(idx)}
                          className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {showAnswers[idx] ? 'Hide Answer' : 'Show Answer'}
                        </button>
                      )}

                      {showAnswers[idx] && !state.evaluated && (
                        <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                          <div className="flex items-start gap-2">
                            <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                                Answer:
                              </p>
                              <p className="text-sm text-blue-800 dark:text-blue-200">
                                {q.answer}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
