
import axios from 'axios';
import { supabase } from './supabase';

const API_URL_RAW = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const API_URL = API_URL_RAW.endsWith('/api') ? API_URL_RAW : `${API_URL_RAW}/api`;

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 120000, // increase default timeout to 120s for slow endpoints
});

// Sync Auth Token from Supabase or Local Storage
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    } else {
        const localToken = localStorage.getItem('access_token');
        if (localToken) {
            config.headers.Authorization = `Bearer ${localToken}`;
        }
    }

    return config;
});

export const apiLogin = async (username, password) => {
    const response = await api.post('/login', { username, password });
    return response.data;
};

export const getInsights = async (productId?: string) => {
    const response = await api.get(`/insights${productId ? `?product_id=${productId}` : ''}`);
    return response.data?.data || [];
};

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
            // Increase timeout to 60 seconds (60000ms) to prevent ECONNABORTED on slow networks
            const response = await api.get('/products', { timeout: 60000 });
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
    ,
    scrapeYoutube: async (url: string, productId?: string) => {
        try {
            const response = await api.post('/scrape/youtube', { url, product_id: productId });
            return response.data || {};
        } catch (e) {
            console.error('scrapeYoutube failed', e);
            throw e;
        }
    }
};


// Re-implementing to support arguments
export const getDashboardStats = async (productId?: string) => {
    try {
        const url = productId ? `/dashboard?product_id=${productId}` : '/dashboard';
        const response = await api.get(url);
        return response.data?.data;
    } catch (e) {
        return null;
    }
};

export const getAnalytics = async (range: string, productId?: string) => {
    try {
        let url = `/analytics?range=${range}`;
        if (productId) url += `&product_id=${productId}`;
        const response = await api.get(url);
        return response.data;
    } catch (e) {
        console.error("Analytics fetch failed", e);
        return { success: false, data: { sentimentTrends: [] } };
    }
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

export const getYoutubeStreamUrl = (url: string, productId?: string, max_results = 50) => {
    const base = API_URL.replace(/\/+$/, '');
    const params = new URLSearchParams();
    params.set('url', url);
    if (productId) params.set('product_id', productId);
    params.set('max_results', String(max_results));
    return `${base}/scrape/youtube/stream?${params.toString()}`;
};

export const getReports = async () => {
    try {
        const response = await api.get('/reports');
        return response.data?.data || [];
    } catch (e) {
        return [];
    }
};

export const downloadReport = async (filename: string) => {
    try {
        const response = await api.get(`/reports/${filename}`, { responseType: 'blob' });
        const contentType = response.headers['content-type'] || 'application/pdf';
        const blob = new Blob([response.data], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
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




export const getTopics = async (limit = 10, productId?: string) => {
    try {
        const params = new URLSearchParams({ limit: String(limit) });
        if (productId) params.append("product_id", productId);
        const response = await api.get(`/topics?${params.toString()}`);
        return response.data?.data || [];
    } catch (e) {
        console.error("getTopics failed", e);
        return [];
    }
};

export const getWordCloud = async (productId?: string) => {
    try {
        const url = productId ? `/products/${productId}/wordcloud` : `/wordcloud`;
        const response = await api.get(url);
        return response.data?.data || {}; // { positive: base64, negative: base64, neutral: base64 }
    } catch (e) {
        console.error("getWordCloud failed", e);
        return {};
    }
};

export const exportReport = async (productId: string, format: 'pdf' | 'excel' | 'csv') => {
    try {
        // Direct download using blob
        const response = await api.get(`/reports/export?product_id=${productId}&format=${format}`, {
            responseType: 'blob'
        });

        const contentType = response.headers['content-type'];
        const blob = new Blob([response.data], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = format === 'excel' ? 'xlsx' : format;
        a.download = `report_${productId}_${new Date().toISOString().split('T')[0]}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        return { success: true };
    } catch (e) {
        console.error("Export failed", e);
        throw e;
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
        const response = await api.get(`/competitors/compare?productA=${idA}&productB=${idB}`);
        return { success: true, data: response.data?.data || { metrics: {} } };
    } catch (e) {
        // Return empty comparison if endpoint not available or error
        return { success: false, data: { metrics: {} } };
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

export const resolveAlert = async (id: string) => {
    try {
        await api.post(`/alerts/${id}/read`);
        return { success: true };
    } catch (e) {
        return { success: false };
    }
};

export const getSystemStatus = async () => {
    try {
        const response = await api.get('/system/status');
        return response.data?.data || { reddit: false, twitter: false, youtube: false, database: false };
    } catch (e) {
        return { reddit: false, twitter: false, youtube: false, database: false };
    }
};


export const getReviews = async (productId: string, limit = 500) => {
    try {
        const response = await api.get('/reviews', { params: { product_id: productId, limit } });
        const data = response.data?.data || [];

        // Normalize data to match Review interface
        return data.map((r: any) => {
            const sa = r.sentiment_analysis?.[0] || r.sentiment_analysis || {};
            return {
                id: r.id,
                text: r.content || r.text || "",
                platform: r.platform,
                username: r.username || "Anonymous",
                sentiment: (sa.label || "neutral").toLowerCase(),
                sentiment_label: sa.label,
                score: sa.score,
                timestamp: r.created_at,
                sourceUrl: r.source_url,
                credibility: sa.credibility,
                like_count: r.like_count || 0,
                reply_count: r.reply_count || 0,
                retweet_count: r.retweet_count || 0
            };
        });
    } catch (e) {
        console.error('getReviews failed', e);
        return [];
    }
};

export const getExportUrl = (productId: string, format: string) => {
    const base = API_URL.replace(/\/+$/, '');
    return `${base}/reports/export?product_id=${productId}&format=${format}`;
};

export const getProductStats = async (productId: string) => {
    try {
        const response = await api.get(`/products/${productId}/stats`);
        return response.data?.data || null;
    } catch (e) {
        console.error('getProductStats failed', e);
        return null;
    }
};

export const createAlert = async (data: any) => {
    const response = await api.post('/alerts', data);
    return response.data;
};

export const updateSettings = async (data: any) => {
    const response = await api.post('/settings', data);
    return response.data;
};

export const getSettings = async () => {
    try {
        const response = await api.get('/settings');
        return response.data?.data;
    } catch (e) {
        return null;
    }
};

export const getPredictions = getPredictiveAnalytics;

export default sentinelApi;

