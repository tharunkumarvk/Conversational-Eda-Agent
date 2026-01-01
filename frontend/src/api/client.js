// src/api/client.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes for large file operations
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    console.log('[API Client] Request to:', config.url, 'Token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Authentication
  googleLogin: (token) => apiClient.post('/api/auth/google', { token }),
  getCurrentUser: () => apiClient.get('/api/auth/me'),
  logout: () => apiClient.post('/api/auth/logout'),

  // File operations
  uploadFile: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
  },

  getDatasets: () => apiClient.get('/api/datasets'),
  
  listDatasets: () => apiClient.get('/api/datasets'),

  getDatasetInfo: (fileId) => apiClient.get(`/api/dataset/${fileId}`),

  deleteDataset: (fileId) => apiClient.delete(`/api/dataset/${fileId}`),

  downloadFile: (fileId) => apiClient.get(`/api/download/${fileId}`, {
    responseType: 'blob',
  }),

  // Plot operations
  getSavedPlots: (fileId) => apiClient.get(`/api/plots/${fileId}`),
  
  downloadAllPlots: (fileId) => apiClient.get(`/api/plots/${fileId}/download`, {
    responseType: 'blob',
  }),
  
  deleteSavedPlots: (fileId) => apiClient.delete(`/api/plots/${fileId}`),

  // Processing operations
  mergeFiles: (data) => apiClient.post('/api/merge', data),

  preprocessFile: (data) => apiClient.post('/api/preprocess', data),

  // Visualization
  getVisualSummary: (fileId) => apiClient.get(`/api/visual_summary/${fileId}`),

  createPlot: (data) => apiClient.post('/api/plot', data),

  // AI Chat
  chat: (data) => apiClient.post('/api/chat', data),

  getChatHistory: (fileId, limit = 20) =>
    apiClient.get(`/api/chat/history/${fileId}?limit=${limit}`),
};

export default apiClient;
