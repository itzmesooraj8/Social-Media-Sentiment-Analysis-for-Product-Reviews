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

    // Simple in-memory/localStorage mock auth for dev when env is missing
    let authCallback: ((event: string, session: any) => void) | null = null;

    const notify = (event: string, session: any) => {
        try {
            if (authCallback) authCallback(event, session);
        } catch (e) {
            // swallow
        }
    };

    supabase = {
        auth: {
            async signUp(email?: string, password?: string) {
                // mimic account creation by delegating to signIn
                const session = { access_token: 'dev-token', user: { id: 'dev-user', email } };
                try { localStorage.setItem('mock_session', JSON.stringify(session)); } catch (e) {}
                notify('SIGNED_IN', session);
                return { data: session, error: null };
            },
            async signInWithPassword({ email, password }: { email?: string, password?: string } = {}) {
                const session = { access_token: 'dev-token', user: { id: 'dev-user', email } };
                try { localStorage.setItem('mock_session', JSON.stringify(session)); } catch (e) {}
                notify('SIGNED_IN', session);
                return { data: session, error: null };
            },
            async signOut() {
                try { localStorage.removeItem('mock_session'); } catch (e) {}
                notify('SIGNED_OUT', null);
                return { error: null };
            },
            async getUser() {
                try {
                    const s = localStorage.getItem('mock_session');
                    const session = s ? JSON.parse(s) : null;
                    return { data: { user: session?.user ?? null } };
                } catch (e) {
                    return { data: { user: null } };
                }
            },
            async getSession() {
                try {
                    const s = localStorage.getItem('mock_session');
                    const session = s ? JSON.parse(s) : null;
                    return { data: { session } };
                } catch (e) {
                    return { data: { session: null } };
                }
            },
            onAuthStateChange(cb?: (event: string, session: any) => void) {
                if (cb) authCallback = cb;
                const subscription = { unsubscribe: () => { authCallback = null; } };
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
