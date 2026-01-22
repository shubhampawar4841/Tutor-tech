import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';

interface SessionState {
  status: 'idle' | 'creating' | 'ready' | 'learning' | 'completed';
  session_id?: string;
  current_index: number;
  total_knowledge_points: number;
  current_html: string;
  current_questions?: any[];
  current_knowledge_point?: any;
  summary?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export function useGuideSession() {
  const [sessionState, setSessionState] = useState<SessionState>({
    status: 'idle',
    current_index: 0,
    total_knowledge_points: 0,
    current_html: '',
  });
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const createSession = useCallback(async (selectedRecords: Set<string>) => {
    if (selectedRecords.size === 0) {
      alert('Please select at least one notebook item');
      return;
    }

    setIsLoading(true);
    setLoadingMessage('Creating learning session...');
    setSessionState(prev => ({ ...prev, status: 'creating' }));

    try {
      // Extract notebook IDs from selected records
      const notebookIds = new Set<string>();
      selectedRecords.forEach(recordKey => {
        const [notebookId] = recordKey.split(':');
        notebookIds.add(notebookId);
      });

      const response = await api.guide.start({
        notebook_ids: Array.from(notebookIds),
        max_points: 5,
      });

      if (response.data.session_id) {
        setSessionState({
          status: 'ready',
          session_id: response.data.session_id,
          current_index: 0,
          total_knowledge_points: response.data.content?.total_knowledge_points || response.data.content?.total_steps || 0,
          current_html: '',
        });
      }
    } catch (error: any) {
      console.error('Failed to create session:', error);
      alert(error.response?.data?.detail || 'Failed to create learning session');
      setSessionState(prev => ({ ...prev, status: 'idle' }));
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  }, []);

  const startLearning = useCallback(async () => {
    if (!sessionState.session_id) return;

    setIsLoading(true);
    setLoadingMessage('Loading learning content...');
    setSessionState(prev => ({ ...prev, status: 'learning' }));

    try {
      const response = await api.guide.get(sessionState.session_id);
      const content = response.data.content;
      const knowledgePoints = content.knowledge_points || content.steps || [];
      
      if (knowledgePoints.length > 0) {
        const firstKp = knowledgePoints[0];
        const html = convertKnowledgePointToHTML(firstKp, 0, knowledgePoints.length);
        
        setSessionState(prev => ({
          ...prev,
          current_html: html,
          current_index: 0,
          total_knowledge_points: knowledgePoints.length,
          current_questions: firstKp.questions || [],
          current_knowledge_point: firstKp,
        }));
      }
    } catch (error: any) {
      console.error('Failed to start learning:', error);
      alert(error.response?.data?.detail || 'Failed to load learning content');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  }, [sessionState.session_id]);

  const nextKnowledge = useCallback(async () => {
    if (!sessionState.session_id) return;

    setIsLoading(true);
    setLoadingMessage('Loading next knowledge point...');

    try {
      const response = await api.guide.next(sessionState.session_id);
      
      if (response.data.status === 'completed') {
        // Fetch summary
        try {
          const summaryResponse = await api.guide.summary(sessionState.session_id);
          setSessionState(prev => ({
            ...prev,
            status: 'completed',
            summary: summaryResponse.data.summary || summaryResponse.data.content?.summary || 'Learning completed!',
          }));
        } catch (e) {
          // Try to get summary from guide content
          try {
            const guideResponse = await api.guide.get(sessionState.session_id);
            const summary = guideResponse.data.content?.summary || 'Learning completed!';
            setSessionState(prev => ({
              ...prev,
              status: 'completed',
              summary: summary,
            }));
          } catch (e2) {
            setSessionState(prev => ({
              ...prev,
              status: 'completed',
              summary: 'Learning completed!',
            }));
          }
        }
      } else {
        // Load next knowledge point
        const guideResponse = await api.guide.get(sessionState.session_id);
        const content = guideResponse.data.content;
        const knowledgePoints = content.knowledge_points || content.steps || [];
        const nextIndex = response.data.current_step || sessionState.current_index + 1;
        
        if (nextIndex < knowledgePoints.length) {
          const nextKp = knowledgePoints[nextIndex];
          const html = convertKnowledgePointToHTML(nextKp, nextIndex, knowledgePoints.length);
          
          setSessionState(prev => ({
            ...prev,
            current_html: html,
            current_index: nextIndex,
            current_questions: nextKp.questions || [],
            current_knowledge_point: nextKp,
          }));
        } else {
          setSessionState(prev => ({
            ...prev,
            status: 'completed',
            summary: 'Learning completed!',
          }));
        }
      }
    } catch (error: any) {
      console.error('Failed to move to next knowledge point:', error);
      alert(error.response?.data?.detail || 'Failed to load next content');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  }, [sessionState.session_id, sessionState.current_index]);

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionState.session_id || !message.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: Date.now(),
    };

    setChatMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.guide.chat(sessionState.session_id, { message });
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer || response.data.response || '',
        timestamp: Date.now(),
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: Date.now(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  }, [sessionState.session_id]);

  const fixHtml = useCallback(async (description: string): Promise<string> => {
    // Simple HTML fix - can be enhanced
    return description;
  }, []);

  const canStart = sessionState.status === 'ready';
  const canNext = sessionState.status === 'learning' && !isLoading;
  const isCompleted = sessionState.status === 'completed';
  const isLastKnowledge = sessionState.current_index >= sessionState.total_knowledge_points - 1;

  return {
    sessionState,
    chatMessages,
    isLoading,
    loadingMessage,
    canStart,
    canNext,
    isCompleted,
    isLastKnowledge,
    createSession,
    startLearning,
    nextKnowledge,
    sendMessage,
    fixHtml,
  };
}

// Helper function to convert knowledge point to HTML
function convertKnowledgePointToHTML(kp: any, index: number, total: number): string {
  const title = kp.knowledge_title || kp.title || `Knowledge Point ${index + 1}`;
  const description = kp.description || '';
  const content = kp.content || '';
  const keyPoints = kp.key_points || [];
  const remedialContent = kp.remedial_content || [];

  return `
    <div class="guide-content">
      <div class="guide-header">
        <h1>${title}</h1>
        <p class="guide-description">${description}</p>
        <div class="guide-progress">Knowledge Point ${index + 1} of ${total}</div>
      </div>
      
      ${keyPoints.length > 0 ? `
        <div class="guide-key-points">
          <h2>Key Points</h2>
          <ul>
            ${keyPoints.map((point: string) => `<li>${point}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      <div class="guide-main-content">
        ${content.split('\n').map((para: string) => 
          para.trim() ? `<p>${para}</p>` : ''
        ).join('')}
      </div>
      
      ${remedialContent.length > 0 ? `
        <div class="guide-remedial">
          <h2>📚 Additional Help</h2>
          ${remedialContent.map((remedial: any, rIdx: number) => `
            <div class="remedial-item">
              <h3>${remedial.title || `Additional Help ${rIdx + 1}`}</h3>
              ${remedial.simplified_explanation ? `
                <div class="remedial-section">
                  <h4>Simplified Explanation</h4>
                  <p>${remedial.simplified_explanation}</p>
                </div>
              ` : ''}
              ${remedial.step_by_step && Array.isArray(remedial.step_by_step) ? `
                <div class="remedial-section">
                  <h4>Step-by-Step Guide</h4>
                  <ol>
                    ${remedial.step_by_step.map((step: string) => `<li>${step}</li>`).join('')}
                  </ol>
                </div>
              ` : ''}
              ${remedial.examples && Array.isArray(remedial.examples) ? `
                <div class="remedial-section">
                  <h4>Examples</h4>
                  <ul>
                    ${remedial.examples.map((ex: string) => `<li>${ex}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
              ${remedial.common_mistakes && Array.isArray(remedial.common_mistakes) ? `
                <div class="remedial-section">
                  <h4>Common Mistakes to Avoid</h4>
                  <ul>
                    ${remedial.common_mistakes.map((mistake: string) => `<li>${mistake}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
              ${remedial.practice_tips && Array.isArray(remedial.practice_tips) ? `
                <div class="remedial-section">
                  <h4>Practice Tips</h4>
                  <ul>
                    ${remedial.practice_tips.map((tip: string) => `<li>${tip}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
              ${remedial.content ? `<p>${remedial.content}</p>` : ''}
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

