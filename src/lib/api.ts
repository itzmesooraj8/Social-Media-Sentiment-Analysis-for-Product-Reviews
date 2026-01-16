import axios from 'axios';
import { supabase } from './supabase';
import { Product, Review, DashboardMetrics } from '../types/sentinel';

// 1. Setup Axios Instance
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    headers: { 'Content-Type': 'application/json' },
});

// 2. Request Interceptor (Adds Auth Token)
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

// 3. Response Interceptor (Error Handling)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Call Failed:', error.config?.url, error.response?.status);
        return Promise.reject(error);
    }
);

// --- API EXPORTS (These were missing!) ---

// Products
export const getProducts = async (): Promise<Product[]> => {
    const { data } = await api.get('/products');
    return data.data || [];
};

export const createProduct = async (productData: Partial<Product>): Promise<Product> => {
    const { data } = await api.post('/products', productData);
    return data.data;
};

export const deleteProduct = async (id: string): Promise<void> => {
    await api.delete(`/products/${id}`);
};

export const updateProduct = async (id: string, updates: Partial<Product>): Promise<Product> => {
    const { data } = await api.put(`/products/${id}`, updates);
    return data.data;
};

export const getProductDetails = async (id: string): Promise<Product> => {
    const { data } = await api.get(`/products/${id}`);
    return data.data;
};

// Reviews & Scraping
export const scrapeReddit = async (productName: string): Promise<any> => {
    const { data } = await api.post('/scrape/reddit', { query: productName });
    return data;
};

export const analyzeUrl = async (url: string): Promise<any> => {
    const { data } = await api.post('/analyze/url', { url });
    return data;
};

// Dashboard & Analytics
export const getDashboardStats = async (): Promise<DashboardMetrics> => { // Renamed to getDashboardStats to match user request, checking usage... user's previous code used getDashboardData. I might need to alias or update hook.
    const { data } = await api.get('/dashboard');
    return data.data;
};

// Helper to keep compatibility if pages use getDashboardData
export const getDashboardData = getDashboardStats;

export const getAnalytics = async (period: string = '7d'): Promise<any> => {
    const { data } = await api.get(`/analytics?period=${period}`);
    return data.data;
};

export const getExecutiveSummary = async () => {
    const response = await api.get('/reports/summary');
    return response.data;
};

// Competitors
export const getCompare = async (productA: string, productB: string): Promise<any> => {
    const { data } = await api.get(`/products/compare?id_a=${productA}&id_b=${productB}`);
    return data.data;
};

// Alerts
export const getAlerts = async (): Promise<any[]> => {
    const { data } = await api.get('/alerts');
    return data.data || [];
};

export const createAlert = async (alertData: any): Promise<any> => {
    const { data } = await api.post('/alerts', alertData);
    return data.data;
};

export const deleteAlert = async (id: string): Promise<void> => {
    await api.delete(`/alerts/${id}`);
};

// Default Export (for generic usage)
export default api;
