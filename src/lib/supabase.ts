import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

// Flag indicating whether Supabase was properly configured via env vars.
// Components can check this to fast-fail or skip Supabase-dependent operations.
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseKey);

let supabase: any;

if (!isSupabaseConfigured) {
    console.warn(
        'CRITICAL: Missing VITE_SUPABASE_URL or VITE_SUPABASE_KEY.\n' +
        'Set these in Vercel → Settings → Environment Variables and redeploy.\n' +
        'Auth will not work until these are set.'
    );
    // Use a known-invalid but structurally-valid URL so createClient() does not throw.
    // All auth calls will fail gracefully; the AuthContext timeout (8s) will unblock the app.
    supabase = createClient(
        'https://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.supabase.co',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwbGFjZWhvbGRlciJ9.placeholder',
        { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } }
    );
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
