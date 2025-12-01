import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// API methods
export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Transactions
  analyzeTransaction: (data) =>
    apiClient.post('/api/transactions/analyze-transaction', data),
  
  batchAnalyze: (formData) =>
    apiClient.post('/api/transactions/batch-analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  getTransactionStats: () =>
    apiClient.get('/api/transactions/stats'),

  // Map
  getMapTransactions: (params) =>
    apiClient.get('/api/map/transactions', { params }),
  
  getMunicipalities: (departamento) =>
    apiClient.get(`/api/map/municipalities/${departamento}`),
  
  getHeatmapData: (params) =>
    apiClient.get('/api/map/heatmap', { params }),

  // Chat
  chatQuery: (data) =>
    apiClient.post('/api/chat/query', data),
  
  getSuggestions: () =>
    apiClient.get('/api/chat/suggestions'),

  // Valuation (Price Prediction)
  predictPrice: (data) =>
    apiClient.post('/api/valuation/predict', data),
  
  getValuationStats: () =>
    apiClient.get('/api/valuation/stats'),
  
  getValuationHealth: () =>
    apiClient.get('/api/valuation/health'),

  // Property Search
  searchProperty: async (matricula) => {
    const response = await apiClient.post('/api/property/search', { matricula });
    return response.data;
  },
  
  getPropertyHealth: () =>
    apiClient.get('/api/property/health'),
}

export default api
