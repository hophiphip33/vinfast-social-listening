/**
 * API Service Layer for VinFast Social Listening Dashboard
 * Handles all HTTP requests to the backend API
 */

import axios from 'axios';

// Configure axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    
    if (error.response?.status === 404) {
      throw new Error('Không tìm thấy tài nguyên');
    } else if (error.response?.status === 500) {
      throw new Error('Lỗi hệ thống, vui lòng thử lại sau');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Kết nối timeout, vui lòng kiểm tra mạng');
    }
    
    throw error;
  }
);

// Health and System APIs
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await api.get('/api/system/status');
  return response.data;
};

// Data Collection APIs
export const startNewsCollection = async () => {
  const response = await api.post('/api/collect/news');
  return response.data;
};

export const startFacebookCollection = async () => {
  const response = await api.post('/api/collect/facebook');
  return response.data;
};

export const startTikTokCollection = async () => {
  const response = await api.post('/api/collect/tiktok');
  return response.data;
};

export const startFullCollection = async () => {
  const response = await api.post('/api/collect/all');
  return response.data;
};

export const startSentimentProcessing = async () => {
  const response = await api.post('/api/process/sentiment');
  return response.data;
};

// Analytics APIs
export const fetchAnalyticsOverview = async (days = 7) => {
  const response = await api.get(`/api/analytics/overview?days=${days}`);
  return response.data;
};

export const fetchRealTimeMetrics = async () => {
  const response = await api.get('/api/analytics/real-time');
  return response.data;
};

export const fetchSentimentTrends = async (days = 30, interval = 'daily') => {
  const response = await api.get(`/api/analytics/sentiment-trends?days=${days}&interval=${interval}`);
  return response.data;
};

export const fetchKeywordAnalysis = async (days = 7, limit = 50) => {
  const response = await api.get(`/api/analytics/keywords?days=${days}&limit=${limit}`);
  return response.data;
};

export const fetchWordCloudData = async (days = 7, limit = 100) => {
  const response = await api.get(`/api/dashboard/wordcloud?days=${days}&limit=${limit}`);
  return response.data;
};

export const fetchDashboardStats = async () => {
  const response = await api.get('/api/dashboard/stats');
  return response.data;
};

// Data Retrieval APIs
export const fetchPosts = async (params = {}) => {
  const {
    platform,
    sentiment,
    days = 7,
    limit = 100
  } = params;
  
  const queryParams = new URLSearchParams();
  if (platform) queryParams.append('platform', platform);
  if (sentiment) queryParams.append('sentiment', sentiment);
  queryParams.append('days', days);
  queryParams.append('limit', limit);
  
  const response = await api.get(`/api/posts?${queryParams}`);
  return response.data;
};

export const fetchPostDetails = async (postId) => {
  const response = await api.get(`/api/posts/${postId}`);
  return response.data;
};

export const searchPosts = async (query, filters = {}) => {
  const queryParams = new URLSearchParams();
  queryParams.append('query', query);
  
  if (filters.platform) queryParams.append('platform', filters.platform);
  if (filters.sentiment) queryParams.append('sentiment', filters.sentiment);
  if (filters.limit) queryParams.append('limit', filters.limit);
  
  const response = await api.get(`/api/search/posts?${queryParams}`);
  return response.data;
};

// Manual Analysis APIs
export const analyzeTextSentiment = async (text) => {
  const response = await api.post('/api/analyze/sentiment', { text });
  return response.data;
};

// Export APIs
export const exportReport = async (days = 30, format = 'json') => {
  const response = await api.get(`/api/export/report?days=${days}&format=${format}`);
  return response.data;
};

// Admin APIs (for development/testing)
export const resetAllData = async () => {
  const response = await api.delete('/api/admin/reset-data');
  return response.data;
};

// Utility functions
export const formatDate = (date) => {
  return new Date(date).toLocaleDateString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatNumber = (number) => {
  return new Intl.NumberFormat('vi-VN').format(number);
};

export const getSentimentColor = (sentiment) => {
  switch (sentiment) {
    case 'positive':
      return '#4caf50';
    case 'negative':
      return '#f44336';
    case 'neutral':
      return '#ff9800';
    default:
      return '#757575';
  }
};

export const getSentimentLabel = (sentiment) => {
  switch (sentiment) {
    case 'positive':
      return 'Tích cực';
    case 'negative':
      return 'Tiêu cực';
    case 'neutral':
      return 'Trung tính';
    default:
      return 'Không xác định';
  }
};

export const getPlatformLabel = (platform) => {
  switch (platform) {
    case 'facebook':
      return 'Facebook';
    case 'tiktok':
      return 'TikTok';
    case 'news':
      return 'Tin tức';
    default:
      return platform;
  }
};

// Error handling utilities
export class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.detail || error.response.data?.message || 'Lỗi server';
    throw new APIError(message, error.response.status, error.response.data);
  } else if (error.request) {
    // Request was made but no response
    throw new APIError('Không thể kết nối đến server', 0, null);
  } else {
    // Something else happened
    throw new APIError(error.message || 'Lỗi không xác định', 0, null);
  }
};

export default api;
