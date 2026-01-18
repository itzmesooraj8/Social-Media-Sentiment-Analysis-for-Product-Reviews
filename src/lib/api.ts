
import axios from 'axios';
import { supabase } from './supabase';

// Ensure this matches your backend URL
const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Sync Auth Token from Supabase
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }

    return config;
});

// Handle 401 Unauthorized errors globally
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            // Force signout if token is invalid
            await supabase.auth.signOut();
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const sentinelApi = {
    // --- Auth & User ---
    // (Assuming basic auth methods exist, preserving if any, otherwise minimal placeholder)
    // If you had previous methods, they should be preserved, but for this specific request:

    // NEW: Strict YouTube Trigger
    scrapeYoutube: async (query: string, productId?: string) => {
        const response = await api.post('/scrape/youtube', {
            query,
            product_id: productId
        });
        return response.data;
    },

    // Ensure these exist for the dashboard to work
    getDashboardStats: async () => {
        const response = await api.get('/dashboard');
        return response.data;
    },

    analyzeText: async (text: string) => {
        const response = await api.post('/analyze', { text });
        return response.data;
    },



    getProducts: async () => {
        try {
            const response = await api.get('/products', { timeout: 8000 });
            return response.data.data || [];
        } catch (e) {
            console.error("API /products failed", e);
            throw e;
        }
    },

    createProduct: async (productData: any) => {
        const response = await api.post('/products', productData);
        return response.data;
    }
};


export const getDashboardStats = sentinelApi.getDashboardStats;
export const getAnalytics = async (range: string) => {
    // Placeholder, map to dashboard stats or specific endpoint if exists
    return sentinelApi.getDashboardStats();
};
export const getExecutiveSummary = async () => {
    try {
        const response = await api.get('/dashboard');
        return { success: true, summary: response.data?.data?.aiSummary || null };
    } catch (e) {
        return { success: false, summary: null };
    }
};

export const getPredictiveAnalytics = async (productId: string, days: number = 7) => {
    try {
        const response = await api.get(`/products/${productId}/predictions?days=${days}`);
        return { success: true, data: response.data?.data || null };
    } catch (e) {
        // Return null if endpoint not available - NO FAKE DATA
        return { success: false, data: null };
    }
};


export const getProducts = sentinelApi.getProducts;
export const createProduct = sentinelApi.createProduct;
export const analyzeText = sentinelApi.analyzeText;
export const scrapeYoutube = sentinelApi.scrapeYoutube;




export const deleteProduct = async (id: string) => {
    try {
        await api.delete(`/products/${id}`);
        return { success: true };
    } catch (e) {
        console.error("Delete failed", e);
        throw e;
    }
};
export const scrapeReddit = async (query: string) => {
    const response = await api.post('/scrape/reddit', { query });
    return response.data;
};
export const scrapeTwitter = async (query: string, productId?: string) => {
    const response = await api.post('/scrape/twitter', { query, product_id: productId });
    return response.data;
};



export const getCompare = async (idA: string, idB: string) => {
    try {
        const response = await api.get(`/compare?productA=${idA}&productB=${idB}`);
        return { success: true, data: response.data?.data || { aspects: [], metrics: {} } };
    } catch (e) {
        // Return empty comparison if endpoint not available
        return { success: false, data: { aspects: [], metrics: {} } };
    }
};


export const getAlerts = async () => {
    try {
        const response = await api.get('/alerts');
        return response.data?.data || [];
    } catch (e) {
        // Return empty array if alerts endpoint not available
        return [];
    }
};

export default sentinelApi;

