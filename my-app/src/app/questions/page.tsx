'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { HelpCircle, Send, Loader2, BookOpen, CheckCircle2, XCircle } from 'lucide-react';
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
                {questions.map((q, idx) => (
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
                        </div>
                        <p className="text-zinc-900 dark:text-zinc-50 font-medium mb-3">
                          {q.question}
                        </p>
                      </div>
                    </div>

                    {q.type === 'multiple_choice' && q.options && q.options.length > 0 && (
                      <div className="ml-4 mb-4">
                        <ul className="space-y-2">
                          {q.options.map((option, optIdx) => {
                            const isCorrect = option === q.answer || 
                              (q.answer && option.toLowerCase().includes(q.answer.toLowerCase()));
                            const showAnswer = showAnswers[idx];
                            
                            return (
                              <li
                                key={optIdx}
                                className={`flex items-center gap-2 p-2 rounded ${
                                  showAnswer && isCorrect
                                    ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                                    : 'bg-zinc-50 dark:bg-zinc-800'
                                }`}
                              >
                                <span className="font-medium text-zinc-600 dark:text-zinc-400 w-6">
                                  {String.fromCharCode(65 + optIdx)}.
                                </span>
                                <span className="flex-1 text-zinc-700 dark:text-zinc-300">
                                  {option}
                                </span>
                                {showAnswer && isCorrect && (
                                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}

                    <button
                      onClick={() => toggleAnswer(idx)}
                      className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {showAnswers[idx] ? 'Hide Answer' : 'Show Answer'}
                    </button>

                    {showAnswers[idx] && (
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
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
