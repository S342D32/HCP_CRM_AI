/**
 * =============================================================================
 * API Service Module
 * =============================================================================
 * This module handles all HTTP requests to the backend API.
 * It uses Axios for HTTP requests and provides a clean interface
 * for all API operations.
 * 
 * Features:
 * - Base URL configuration
 * - Request/response interceptors
 * - Error handling
 * - All API endpoints organized by feature
 */

import axios from 'axios';

// =============================================================================
// Axios Instance Configuration
// =============================================================================
const api = axios.create({
    // Relative path — Vite dev server proxies /api to Flask on port 5000
    // This means no CORS issues at all in development
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 300000,
});

// =============================================================================
// Request Interceptor - Add any auth tokens or modify requests
// =============================================================================
api.interceptors.request.use(
    (config) => {
        // You can add authentication tokens here if needed
        // const token = localStorage.getItem('token');
        // if (token) {
        //     config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// =============================================================================
// Response Interceptor - Handle common error responses
// =============================================================================
api.interceptors.response.use(
    (response) => {
        // Return successful responses as-is
        return response.data;
    },
    (error) => {
        // Extract error message from response
        const message = error.response?.data?.error || 
                       error.message || 
                       'An unexpected error occurred';
        
        console.error('API Error:', message);
        return Promise.reject(new Error(message));
    }
);

// =============================================================================
// Chat API Methods
// =============================================================================
export const chatAPI = {
    /**
     * Send a message to the AI chat agent
     * @param {string} message - User's message
     * @param {Array} chatHistory - Previous conversation history
     * @returns {Promise} - AI response with tool calls and results
     */
    sendMessage: async (message, chatHistory = []) => {
        return api.post('/chat', {
            message,
            chat_history: chatHistory
        });
    }
};

// =============================================================================
// Interaction API Methods
// =============================================================================
export const interactionAPI = {
    /**
     * Get all interactions with optional filters
     * @param {Object} params - Query parameters for filtering
     * @returns {Promise} - Paginated list of interactions
     */
    getAll: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        // Build query string from params
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        const url = queryString ? `/interactions?${queryString}` : '/interactions';
        
        return api.get(url);
    },
    
    /**
     * Get a single interaction by ID
     * @param {number} id - Interaction ID
     * @returns {Promise} - Interaction details
     */
    getById: async (id) => {
        return api.get(`/interactions/${id}`);
    },
    
    /**
     * Create a new interaction (form submission)
     * @param {Object} interactionData - Interaction data
     * @returns {Promise} - Created interaction
     */
    create: async (interactionData) => {
        return api.post('/interactions', interactionData);
    },
    
    /**
     * Update an existing interaction
     * @param {number} id - Interaction ID
     * @param {Object} updateData - Fields to update
     * @returns {Promise} - Updated interaction
     */
    update: async (id, updateData) => {
        return api.put(`/interactions/${id}`, updateData);
    },
    
    /**
     * Delete an interaction
     * @param {number} id - Interaction ID
     * @returns {Promise} - Deletion confirmation
     */
    delete: async (id) => {
        return api.delete(`/interactions/${id}`);
    }
};

// =============================================================================
// HCP API Methods
// =============================================================================
export const hcpAPI = {
    /**
     * Get all Healthcare Professionals
     * @returns {Promise} - List of HCPs
     */
    getAll: async () => {
        return api.get('/hcps');
    },
    
    /**
     * Create a new HCP
     * @param {Object} hcpData - HCP data
     * @returns {Promise} - Created HCP
     */
    create: async (hcpData) => {
        return api.post('/hcps', hcpData);
    }
};

// =============================================================================
// Health Check
// =============================================================================
export const healthAPI = {
    /**
     * Check if API is healthy
     * @returns {Promise} - Health status
     */
    check: async () => {
        return api.get('/health');
    }
};

// Export all APIs as default
export default {
    chat: chatAPI,
    interactions: interactionAPI,
    hcps: hcpAPI,
    health: healthAPI
};