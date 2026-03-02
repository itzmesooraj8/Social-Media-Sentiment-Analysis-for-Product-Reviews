
import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import { Session, User } from '@supabase/supabase-js';

interface AuthContextType {
    user: User | null;
    session: Session | null;
    loading: boolean;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    session: null,
    loading: true,
    signOut: async () => { },
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // If Supabase env vars are missing, fast-fail immediately
        if (!isSupabaseConfigured) {
            console.warn('Supabase not configured – skipping auth check. Set VITE_SUPABASE_URL and VITE_SUPABASE_KEY in Vercel.');
            setLoading(false);
            return;
        }

        let cancelled = false;

        // Safety net: if auth never resolves in 8 seconds, unblock the app
        // This prevents infinite loading when Supabase is misconfigured or unreachable
        const authTimeout = setTimeout(() => {
            if (!cancelled) {
                console.warn('Auth initialization timed out – proceeding as unauthenticated');
                setLoading(false);
            }
        }, 8000);

        // Check active sessions and sets the user
        const getSession = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession();
                if (!cancelled) {
                    if (session) {
                        setSession(session);
                        setUser(session.user);
                    } else {
                        setSession(null);
                        setUser(null);
                    }
                    setLoading(false);
                    clearTimeout(authTimeout);
                }
            } catch (err) {
                console.warn('Auth session check failed:', err);
                if (!cancelled) {
                    setSession(null);
                    setUser(null);
                    setLoading(false);
                    clearTimeout(authTimeout);
                }
            }
        };

        getSession();

        // Listen for changes on auth state (logged in, signed out, etc.)
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!cancelled) {
                setSession(session);
                setUser(session?.user ?? null);
                setLoading(false);
                clearTimeout(authTimeout);
            }
        });

        return () => {
            cancelled = true;
            clearTimeout(authTimeout);
            subscription.unsubscribe();
        };
    }, []);

    const signOut = async () => {
        await supabase.auth.signOut();
    };

    return (
        <AuthContext.Provider value={{ user, session, loading, signOut }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
