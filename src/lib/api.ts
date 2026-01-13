/**
 * API client for frontend-backend communication.
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 5000, // 5 second timeout
});

// Response interceptor for error handling
import { supabase } from '@/lib/supabase';

apiClient.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // Silent error handling - just return rejected promise
        return Promise.reject({
            message: error.response?.data?.detail || error.message || 'API request failed',
            status: error.response?.status,
            data: error.response?.data
        });
    }
);

// Sentiment Analysis
export const analyzeSentiment = async (text: string) => {
    const response = await apiClient.post('/api/analyze', { text });
    return response.data;
};

// Products
export const getProducts = async () => {
    const response = await apiClient.get('/api/products');
    return response.data;
};

export const createProduct = async (productData: {
    name: string;
    sku: string;
    category: string;
    description?: string;
    keywords?: string[];
}) => {
    const response = await apiClient.post('/api/products', productData);
    return response.data;
};

export const deleteProduct = async (productId: string) => {
    const response = await apiClient.delete(`/api/products/${productId}`);
    return response.data;
};

// Reviews
export const getReviews = async (productId?: string, limit: number = 100) => {
    const params = new URLSearchParams();
    if (productId) params.append('product_id', productId);
    params.append('limit', limit.toString());

    const response = await apiClient.get(`/api/reviews?${params.toString()}`);
    return response.data;
};

export const createReview = async (reviewData: {
    product_id: string;
    text: string;
    platform: string;
    source_url?: string;
}) => {
    const response = await apiClient.post('/api/reviews', reviewData);
    return response.data;
};

// Dashboard
export const getDashboardData = async () => {
    const response = await apiClient.get('/api/dashboard');
    return response.data;
};

// Analytics
export const getAnalytics = async () => {
    const response = await apiClient.get('/api/analytics');
    return response.data;
};

// Integrations
export const getIntegrations = async () => {
    const response = await apiClient.get('/api/integrations');
    return response.data;
};

// Health Check
export const healthCheck = async () => {
    const response = await apiClient.get('/health');
    return response.data;
};

// Reddit Scraping
export const scrapeReddit = async (productId: string, productName: string, subreddits?: string[]) => {
    const response = await apiClient.post('/api/scrape/reddit', null, {
        params: {
            product_id: productId,
            product_name: productName,
            subreddits: subreddits?.join(',')
        }
    });
    return response.data;
};

export default apiClient;
