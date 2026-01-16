'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { BookOpen, Plus, Upload, Trash2, FileText, Search, Settings, Loader2, CheckCircle, XCircle, X, MessageSquare, Send } from 'lucide-react';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  status: string;
  document_count: number;
  chunk_count?: number;
  processing?: boolean;
}

interface Document {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  status: 'processing' | 'ready' | 'failed';
  chunks_count?: number;
  uploaded_at: string;
}

export default function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDescription, setNewKBDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const createFileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [createDragActive, setCreateDragActive] = useState(false);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<any[]>([]);

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  useEffect(() => {
    if (selectedKB) {
      loadDocuments(selectedKB.id);
      
      // Auto-refresh documents every 3 seconds to check processing status
      const interval = setInterval(async () => {
        await loadDocuments(selectedKB.id);
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [selectedKB]);

  const loadKnowledgeBases = async () => {
    try {
      const response = await api.knowledgeBase.list();
      setKnowledgeBases(response.data.knowledge_bases || []);
    } catch (error) {
      console.error('Failed to load knowledge bases:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async (kbId: string) => {
    try {
      console.log(`Loading documents for knowledge base ${kbId}...`);
      const response = await api.knowledgeBase.getDocuments(kbId);
      const docs = response.data.documents || [];
      console.log(`Loaded ${docs.length} document(s)`, docs);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    }
  };

  const handleCreate = async () => {
    if (!newKBName.trim()) return;
    
    setUploading(true);
    try {
      // Create knowledge base
      const response = await api.knowledgeBase.create({
        name: newKBName,
        description: newKBDescription,
      });
      
      const kbId = response.data.id;
      
      // Upload files if any selected
      if (selectedFiles.length > 0) {
        try {
          console.log(`Uploading ${selectedFiles.length} file(s) to new knowledge base ${kbId}...`);
          const uploadResponse = await api.knowledgeBase.upload(kbId, selectedFiles);
          console.log('Upload response:', uploadResponse.data);
          
          if (uploadResponse.data && uploadResponse.data.files) {
            const uploadedCount = uploadResponse.data.files.length;
            console.log(`Successfully uploaded ${uploadedCount} file(s)`);
          }
        } catch (uploadError: any) {
          console.error('Failed to upload files:', uploadError);
          const errorMessage = uploadError.response?.data?.detail || uploadError.message || 'Unknown error';
          // KB is created, but files failed - show warning
          alert(`Knowledge base created, but file upload failed: ${errorMessage}. You can upload them later.`);
        }
      }
      
      setShowCreateModal(false);
      setNewKBName('');
      setNewKBDescription('');
      setSelectedFiles([]);
      loadKnowledgeBases();
      
      // Auto-select the newly created KB
      const newKB = {
        id: kbId,
        name: newKBName,
        description: newKBDescription,
        status: 'created',
        document_count: selectedFiles.length,
      };
      setSelectedKB(newKB as KnowledgeBase);
    } catch (error) {
      console.error('Failed to create knowledge base:', error);
      alert('Failed to create knowledge base. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files);
    setSelectedFiles((prev) => [...prev, ...fileArray]);
  };

  const handleCreateDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setCreateDragActive(true);
    } else if (e.type === 'dragleave') {
      setCreateDragActive(false);
    }
  };

  const handleCreateDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setCreateDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleCreateFileSelect(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this knowledge base?')) {
      try {
        await api.knowledgeBase.delete(id);
        if (selectedKB?.id === id) {
          setSelectedKB(null);
          setDocuments([]);
        }
        loadKnowledgeBases();
      } catch (error) {
        console.error('Failed to delete knowledge base:', error);
      }
    }
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    if (!selectedKB) {
      alert('Please select a knowledge base first or create a new one.');
      setShowUploadModal(false);
      return;
    }
    
    setUploading(true);
    try {
      const fileArray = Array.from(files);
      console.log(`Uploading ${fileArray.length} file(s) to knowledge base ${selectedKB.id}...`);
      
      const response = await api.knowledgeBase.upload(selectedKB.id, fileArray);
      
      console.log('Upload response:', response.data);
      
      if (response.data && response.data.files) {
        const uploadedCount = response.data.files.length;
        console.log(`Successfully uploaded ${uploadedCount} file(s)`);
        
        // Close modal and refresh
        setShowUploadModal(false);
        
      // Reload documents to show the newly uploaded files
      await loadDocuments(selectedKB.id);
      await loadKnowledgeBases(); // Refresh to update document count
      
      // Show success message
      alert(`Successfully uploaded ${uploadedCount} file(s)! Processing will start automatically.`);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error: any) {
      console.error('Failed to upload files:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload files. Please try again.';
      alert(`Upload failed: ${errorMessage}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="px-4 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                Knowledge Base
              </h1>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                Upload and manage your documents
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              Create Knowledge Base
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12">Loading...</div>
          ) : knowledgeBases.length === 0 ? (
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-12">
              <div className="text-center">
                <BookOpen className="mx-auto h-16 w-16 text-blue-500 mb-4" />
                <h3 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 mb-2">
                  Get Started with Knowledge Base
                </h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                  Create a knowledge base to upload and manage your PDF documents
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-5 w-5 mr-2" />
                  Create Your First Knowledge Base
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Quick Upload Section */}
              {knowledgeBases.length > 0 && (
                <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-1">
                        Ready to upload PDFs?
                      </h3>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">
                        Select a knowledge base below and click "Upload PDF" to get started
                      </p>
                    </div>
                    {selectedKB && (
                      <button
                        onClick={() => setShowUploadModal(true)}
                        className="inline-flex items-center px-5 py-2.5 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                      >
                        <Upload className="h-5 w-5 mr-2" />
                        Upload PDF to {selectedKB.name}
                      </button>
                    )}
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-8">
              {knowledgeBases.map((kb) => (
                <div
                  key={kb.id}
                  className={`bg-white dark:bg-zinc-900 rounded-lg shadow p-6 transition-all hover:shadow-lg border-2 ${
                    selectedKB?.id === kb.id 
                      ? 'ring-2 ring-blue-500 border-blue-500' 
                      : 'border-transparent hover:border-blue-200 dark:hover:border-blue-800'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div 
                      className="flex-1 cursor-pointer"
                      onClick={() => setSelectedKB(kb)}
                    >
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-blue-500" />
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">
                          {kb.name}
                        </h3>
                      </div>
                      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                        {kb.description || 'No description'}
                      </p>
                      <div className="mt-4 flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
                        <span className="flex items-center gap-1">
                          <FileText className="h-4 w-4" />
                          {kb.document_count} documents
                        </span>
                        {kb.chunk_count !== undefined && (
                          <span className="flex items-center gap-1">
                            <Search className="h-4 w-4" />
                            {kb.chunk_count} chunks
                          </span>
                        )}
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        {getStatusIcon(kb.status)}
                        <span className="text-xs capitalize text-zinc-500 dark:text-zinc-400">
                          {kb.status}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2 ml-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedKB(kb);
                          setShowUploadModal(true);
                        }}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
                        title="Upload PDF or documents"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload PDF
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(kb.id);
                        }}
                        className="text-zinc-400 hover:text-red-600 p-1"
                        title="Delete knowledge base"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              </div>
            </>
          )}

          {/* Selected KB Details */}
          {selectedKB && (
            <div className="mt-8 bg-white dark:bg-zinc-900 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                    {selectedKB.name}
                  </h2>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                    {selectedKB.description || 'No description'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setShowUploadModal(true);
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Documents
                  </button>
                  <button className="inline-flex items-center px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-700">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </button>
                </div>
              </div>

              {/* Documents List */}
              <div className="p-6">
                <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-50 mb-4">
                  Documents
                </h3>
                {documents.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
                    <FileText className="mx-auto h-12 w-12 mb-2" />
                    <p>No documents uploaded yet</p>
                    <p className="text-sm mt-1 mb-4">Upload PDFs, text files, or markdown files</p>
                    <button
                      onClick={() => setShowUploadModal(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Upload PDF Now
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-4 border border-zinc-200 dark:border-zinc-700 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <FileText className="h-5 w-5 text-zinc-400" />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                              {doc.filename}
                            </p>
                            <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                              <span>{formatFileSize(doc.size)}</span>
                              <span>•</span>
                              <span className="uppercase">{doc.file_type}</span>
                              {doc.chunks_count !== undefined && (
                                <>
                                  <span>•</span>
                                  <span className={doc.chunks_count > 0 ? 'text-green-600 dark:text-green-400' : 'text-zinc-400'}>
                                    {doc.chunks_count} chunks
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(doc.status)}
                            <span className="text-xs capitalize text-zinc-500 dark:text-zinc-400">
                              {doc.status}
                            </span>
                          </div>
                          {doc.status === 'processing' && (
                            <button
                              onClick={async () => {
                                if (!selectedKB) return;
                                try {
                                  const response = await api.knowledgeBase.processDocument(selectedKB.id, doc.id);
                                  alert(`Processing triggered! ${response.data.chunk_count || 0} chunks created.`);
                                  loadDocuments(selectedKB.id);
                                } catch (error: any) {
                                  alert(`Processing failed: ${error.response?.data?.detail || error.message}`);
                                }
                              }}
                              className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50"
                              title="Manually trigger processing"
                            >
                              Retry Process
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
              <h2 className="text-xl font-bold mb-4 text-zinc-900 dark:text-zinc-50">
                Create Knowledge Base & Upload PDFs
              </h2>
              <div className="space-y-6">
                {/* KB Details */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={newKBName}
                      onChange={(e) => setNewKBName(e.target.value)}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                      placeholder="My Knowledge Base"
                      disabled={uploading}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                      Description
                    </label>
                    <textarea
                      value={newKBDescription}
                      onChange={(e) => setNewKBDescription(e.target.value)}
                      className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
                      rows={2}
                      placeholder="Optional description"
                      disabled={uploading}
                    />
                  </div>
                </div>

                {/* File Upload Section */}
                <div>
                  <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Upload PDF Documents <span className="text-zinc-400 font-normal">(Optional)</span>
                  </label>
                  <div
                    onDragEnter={handleCreateDrag}
                    onDragLeave={handleCreateDrag}
                    onDragOver={handleCreateDrag}
                    onDrop={handleCreateDrop}
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                      createDragActive
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600'
                    }`}
                  >
                    <FileText className="mx-auto h-12 w-12 text-blue-500 mb-3" />
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
                      Drag and drop PDF files here, or
                    </p>
                    <input
                      ref={createFileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.txt,.md,.doc,.docx"
                      onChange={(e) => handleCreateFileSelect(e.target.files)}
                      className="hidden"
                      disabled={uploading}
                    />
                    <button
                      type="button"
                      onClick={() => createFileInputRef.current?.click()}
                      disabled={uploading}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Choose PDF Files
                    </button>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-3">
                      Supported: PDF, TXT, MD, DOC, DOCX
                    </p>
                  </div>

                  {/* Selected Files List */}
                  {selectedFiles.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Selected Files ({selectedFiles.length}):
                      </p>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {selectedFiles.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-2 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700"
                          >
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <FileText className="h-4 w-4 text-zinc-400 flex-shrink-0" />
                              <span className="text-sm text-zinc-700 dark:text-zinc-300 truncate">
                                {file.name}
                              </span>
                              <span className="text-xs text-zinc-500 dark:text-zinc-400 flex-shrink-0">
                                ({formatFileSize(file.size)})
                              </span>
                            </div>
                              <button
                              type="button"
                              onClick={() => removeFile(index)}
                              disabled={uploading}
                              className="text-red-500 hover:text-red-700 ml-2 flex-shrink-0 p-1"
                              title="Remove file"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewKBName('');
                    setNewKBDescription('');
                    setSelectedFiles([]);
                  }}
                  disabled={uploading}
                  className="px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newKBName.trim() || uploading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
                      Create & Upload
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 max-w-2xl w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-zinc-900 dark:text-zinc-50">
                {selectedKB ? `Upload Documents to ${selectedKB.name}` : 'Upload PDF Documents'}
              </h2>
              {!selectedKB && (
                <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    Please select a knowledge base first, or create a new one.
                  </p>
                </div>
              )}
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
                Upload PDFs, text files, or markdown files. Files will be processed and made searchable.
              </p>
              
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600'
                }`}
              >
                <div className="mb-4">
                  <FileText className="mx-auto h-16 w-16 text-blue-500 mb-2" />
                  <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-1">
                    Upload PDF Documents
                  </p>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-4">
                    Drag and drop your PDF files here, or click to browse
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.txt,.md,.doc,.docx"
                  onChange={(e) => handleFileSelect(e.target.files)}
                  className="hidden"
                />
                <button
                  onClick={() => {
                    if (!selectedKB) {
                      alert('Please select a knowledge base first or create a new one.');
                      setShowUploadModal(false);
                      return;
                    }
                    fileInputRef.current?.click();
                  }}
                  disabled={uploading || !selectedKB}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Uploading PDFs...
                    </>
                  ) : (
                    <>
                      <Upload className="h-5 w-5 mr-2" />
                      Choose PDF Files
                    </>
                  )}
                </button>
                {uploading && (
                  <p className="text-sm text-blue-600 dark:text-blue-400 mt-3">
                    Uploading files to server... Please wait.
                  </p>
                )}
                <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">
                    Supported file formats:
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                      PDF
                    </span>
                    <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded text-xs">
                      TXT
                    </span>
                    <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded text-xs">
                      MD
                    </span>
                    <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded text-xs">
                      DOC
                    </span>
                    <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded text-xs">
                      DOCX
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowUploadModal(false)}
                  disabled={uploading}
                  className="px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


