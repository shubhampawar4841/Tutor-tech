/**
 * API Client for DeepTutor Backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://tutor-tech.onrender.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
export const api = {
  // Knowledge Base
  knowledgeBase: {
    list: () => apiClient.get('/api/v1/knowledge-base/'),
    create: (data: { name: string; description?: string }) =>
      apiClient.post('/api/v1/knowledge-base/', data),
    get: (id: string) => apiClient.get(`/api/v1/knowledge-base/${id}`),
    getDocuments: (id: string) => apiClient.get(`/api/v1/knowledge-base/${id}/documents`),
    getChunks: (kbId: string, docId: string) =>
      apiClient.get(`/api/v1/knowledge-base/${kbId}/documents/${docId}/chunks`),
    processDocument: (kbId: string, docId: string) =>
      apiClient.post(`/api/v1/knowledge-base/${kbId}/documents/${docId}/process`),
    upload: (id: string, files: File[]) => {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      return apiClient.post(`/api/v1/knowledge-base/${id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    delete: (id: string) => apiClient.delete(`/api/v1/knowledge-base/${id}`),
    deleteDocument: (kbId: string, docId: string) =>
      apiClient.delete(`/api/v1/knowledge-base/${kbId}/documents/${docId}`),
    ask: (kbId: string, data: {
      question: string;
      top_k?: number;
      threshold?: number;
      model?: string;
    }) => apiClient.post(`/api/v1/knowledge-base/${kbId}/ask`, data),
  },

  // Solve
  solve: {
    start: (data: {
      question: string;
      knowledge_base_id?: string;
      use_web_search?: boolean;
      use_code_execution?: boolean;
    }) => apiClient.post('/api/v1/solve/start', data),
    getStatus: (solveId: string) =>
      apiClient.get(`/api/v1/solve/${solveId}/status`),
    getResult: (solveId: string) =>
      apiClient.get(`/api/v1/solve/${solveId}/result`),
  },

  // Question
  question: {
    generate: (data: {
      knowledge_base_id: string;
      topic: string;
      difficulty?: string;
      question_type?: string;
      count?: number;
    }) => apiClient.post('/api/v1/question/generate', data),
    mimic: (data: { knowledge_base_id: string }, file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post('/api/v1/question/mimic', formData, {
        params: data,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    get: (questionId: string) =>
      apiClient.get(`/api/v1/question/${questionId}`),
  },

  // Research
  research: {
    start: (data: {
      topic: string;
      knowledge_base_id?: string;
      mode?: string;
      max_subtopics?: number;
      execution_mode?: string;
    }) => apiClient.post('/api/v1/research/start', data),
    getStatus: (researchId: string) =>
      apiClient.get(`/api/v1/research/${researchId}/status`),
    getResult: (researchId: string) =>
      apiClient.get(`/api/v1/research/${researchId}/result`),
  },

  // Notebook
  notebook: {
    list: () => apiClient.get('/api/v1/notebook/'),
    create: (data: {
      name: string;
      description?: string;
      color?: string;
      icon?: string;
    }) => apiClient.post('/api/v1/notebook/', data),
    get: (id: string) => apiClient.get(`/api/v1/notebook/${id}`),
    addItem: (id: string, item: any) =>
      apiClient.post(`/api/v1/notebook/${id}/items`, item),
    deleteItem: (id: string, itemId: string) =>
      apiClient.delete(`/api/v1/notebook/${id}/items/${itemId}`),
    delete: (id: string) => apiClient.delete(`/api/v1/notebook/${id}`),
  },

  // Guide
  guide: {
    start: (data: { notebook_ids: string[]; max_points?: number }) =>
      apiClient.post('/api/v1/guide/start', data),
    get: (sessionId: string) =>
      apiClient.get(`/api/v1/guide/${sessionId}`),
    next: (sessionId: string) =>
      apiClient.post(`/api/v1/guide/${sessionId}/next`),
  },

  // Co-Writer
  coWriter: {
    rewrite: (data: {
      text: string;
      instruction: string;
      use_rag?: boolean;
      knowledge_base_id?: string;
    }) => apiClient.post('/api/v1/co-writer/rewrite', data),
    shorten: (data: { text: string; instruction: string }) =>
      apiClient.post('/api/v1/co-writer/shorten', data),
    expand: (data: { text: string; instruction: string }) =>
      apiClient.post('/api/v1/co-writer/expand', data),
    narrate: (data: { text: string; voice?: string }) =>
      apiClient.post('/api/v1/co-writer/narrate', data),
  },

  // Chat
  chat: {
    listSessions: () => apiClient.get('/api/v1/chat/sessions'),
    createSession: () => apiClient.post('/api/v1/chat/sessions'),
    getSession: (sessionId: string) =>
      apiClient.get(`/api/v1/chat/sessions/${sessionId}`),
    sendMessage: (sessionId: string, data: {
      message: string;
      knowledge_base_id?: string;
      use_rag?: boolean;
      use_web_search?: boolean;
    }) =>
      apiClient.post(`/api/v1/chat/sessions/${sessionId}/message`, data),
  },

  // Dashboard
  dashboard: {
    getStats: () => apiClient.get('/api/v1/dashboard/stats'),
    getRecent: () => apiClient.get('/api/v1/dashboard/recent'),
  },

  // IdeaGen
  ideagen: {
    generate: (data: {
      notebook_ids?: string[];
      domain?: string;
      count?: number;
      idea_type?: string;
    }) => apiClient.post('/api/v1/ideagen/generate', data),
  },
};

export default apiClient;


