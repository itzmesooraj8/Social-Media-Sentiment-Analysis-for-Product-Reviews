
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

        // Decode a JWT token and return the payload, or null if invalid/expired.
        const decodeJwt = (token: string): any => {
            try {
                const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                const payload = JSON.parse(atob(b64));
                // Check expiry (exp is in seconds)
                if (payload.exp && payload.exp * 1000 < Date.now()) return null;
                return payload;
            } catch {
                return null;
            }
        };

        // Check active sessions and sets the user
        const getSession = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession();
                if (!cancelled) {
                    if (session) {
                        setSession(session);
                        setUser(session.user);
                    } else {
                        // Supabase has no session — check for a backend JWT in localStorage.
                        // This is set when logging in via the custom /api/login endpoint.
                        const localToken = localStorage.getItem('access_token');
                        const payload = localToken ? decodeJwt(localToken) : null;
                        if (payload) {
                            // Create a minimal synthetic user so ProtectedRoute lets the user through.
                            const syntheticUser: any = {
                                id: payload.user_id || payload.sub || 'backend-user',
                                email: payload.email || payload.sub || '',
                                role: payload.role || 'authenticated',
                                app_metadata: {},
                                user_metadata: {},
                                aud: 'authenticated',
                                created_at: '',
                            };
                            setUser(syntheticUser);
                        } else {
                            // No valid token anywhere — clear stale localStorage entry
                            if (localToken) localStorage.removeItem('access_token');
                            setSession(null);
                            setUser(null);
                        }
                    }
                    setLoading(false);
                    clearTimeout(authTimeout);
                }
            } catch (err) {
                console.warn('Auth session check failed:', err);
                if (!cancelled) {
                    // Even on error, fall back to localStorage token
                    const localToken = localStorage.getItem('access_token');
                    const payload = localToken ? (() => {
                        try {
                            const b64 = localToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                            const p = JSON.parse(atob(b64));
                            return p.exp && p.exp * 1000 < Date.now() ? null : p;
                        } catch { return null; }
                    })() : null;
                    if (payload) {
                        setUser({ id: payload.user_id || payload.sub || 'backend-user', email: payload.email || '', role: 'authenticated', app_metadata: {}, user_metadata: {}, aud: 'authenticated', created_at: '' } as any);
                    } else {
                        setSession(null);
                        setUser(null);
                    }
                    setLoading(false);
                    clearTimeout(authTimeout);
                }
            }
        };

        getSession();

        // Listen for changes on auth state (logged in, signed out, etc.)
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!cancelled) {
                if (session?.user) {
                    // Real Supabase session — use it
                    setSession(session);
                    setUser(session.user);
                } else {
                    // No Supabase session — preserve any backend JWT user rather
                    // than wiping them out. Only clear if localStorage is also empty.
                    const localToken = localStorage.getItem('access_token');
                    const payload = localToken ? (() => {
                        try {
                            const b64 = localToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                            const p = JSON.parse(atob(b64));
                            return p.exp && p.exp * 1000 < Date.now() ? null : p;
                        } catch { return null; }
                    })() : null;

                    if (payload) {
                        // Keep (or restore) synthetic user from backend token
                        setSession(null);
                        setUser((prev: any) => prev ?? {
                            id: payload.user_id || payload.sub || 'backend-user',
                            email: payload.email || '',
                            role: 'authenticated',
                            app_metadata: {},
                            user_metadata: {},
                            aud: 'authenticated',
                            created_at: '',
                        });
                    } else {
                        // Truly unauthenticated
                        setSession(null);
                        setUser(null);
                    }
                }
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
        localStorage.removeItem('access_token');
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
