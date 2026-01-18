
import axios from 'axios';
import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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

    // --- Core API methods ---
    getDashboardStats: async (): Promise<any> => {
        const response = await api.get('/dashboard');
        return response.data;
    },

    triggerScrape: async (productId: string) => {
        const response = await api.post('/scrape/trigger', { product_id: productId });
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

export const downloadReport = async (productId: string) => {
    try {
        const response = await api.get(`/reports/${productId}`, { responseType: 'blob' });
        const contentType = response.headers['content-type'] || 'application/pdf';
        const blob = new Blob([response.data], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sentinel_report_${productId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        return { success: true };
    } catch (e) {
        console.error('downloadReport failed', e);
        return { success: false, error: e };
    }
};




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

export const triggerScrape = async (productId: string) => {
    return sentinelApi.triggerScrape(productId);
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

export const getReviews = async (productId: string, limit = 500) => {
    try {
        const response = await api.get('/reviews', { params: { product_id: productId, limit } });
        return response.data?.data || [];
    } catch (e) {
        console.error('getReviews failed', e);
        return [];
    }
};

export default sentinelApi;

