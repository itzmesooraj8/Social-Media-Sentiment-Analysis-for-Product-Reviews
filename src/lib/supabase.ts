import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

let supabase: any;

if (!supabaseUrl || !supabaseKey) {
    // In dev environments .env may be missing. Don't throw — provide a noop fallback
    // so the app can render and pages that require auth can handle lack of session.
    console.warn('Supabase environment variables not found — using noop fallback client.');

    const noop = () => ({
        data: null,
        error: null,
        async json() { return null; }
    });

    const fallbackChannel = () => ({
        on: () => ({ subscribe: () => ({ unsubscribe: () => {} }) }),
        subscribe: () => ({ unsubscribe: () => {} })
    });

    supabase = {
        auth: {
            async signUp() { return { data: null, error: null }; },
            async signInWithPassword() { return { data: null, error: null }; },
            async signOut() { return { error: null }; },
            async getUser() { return { data: { user: null } }; },
            async getSession() { return { data: { session: null } }; },
            onAuthStateChange() {
                // Return an object shaped like the real client: { data: { subscription } }
                const subscription = { unsubscribe: () => { /* noop */ } };
                return { data: { subscription } };
            }
        },
        from: () => ({ select: async () => ({ data: [], error: null }) }),
        table: () => ({ select: async () => ({ data: [], error: null }), insert: async () => ({ data: [], error: null }) }),
        channel: fallbackChannel,
        rpc: async () => ({ data: null, error: null }),
    };
} else {
    supabase = createClient(supabaseUrl, supabaseKey);
}

export { supabase };

// Auth helpers
export const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
        email,
        password,
    });
    return { data, error };
};

export const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
    });
    return { data, error };
};

export const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    return { error };
};

export const getCurrentUser = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
};

export const subscribeToTable = (table: string, callback: (payload: any) => void) => {
    return supabase
        .channel(`public:${table}`)
        .on('postgres_changes', { event: '*', schema: 'public', table: table }, callback)
        .subscribe();
};
