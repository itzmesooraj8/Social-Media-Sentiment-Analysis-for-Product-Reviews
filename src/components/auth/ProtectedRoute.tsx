
import { useNavigate } from 'react-router-dom';
import { Loader2, WifiOff } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useEffect, useState } from 'react';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
    const navigate = useNavigate();
    const { user, loading } = useAuth();
    const [slowLoad, setSlowLoad] = useState(false);

    // After 5s still loading → show a "backend waking up" hint
    useEffect(() => {
        if (!loading) return;
        const t = setTimeout(() => setSlowLoad(true), 5000);
        return () => clearTimeout(t);
    }, [loading]);

    useEffect(() => {
        if (!loading && !user) {
            navigate('/login');
        }
    }, [user, loading, navigate]);

    if (loading) {
        return (
            <div className="h-screen w-full flex flex-col items-center justify-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Initializing Sentinel…</p>
                {slowLoad && (
                    <div className="flex flex-col items-center gap-2 mt-2 text-center max-w-xs">
                        <WifiOff className="h-5 w-5 text-muted-foreground opacity-60" />
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            The backend may be waking up from sleep (Render free-tier).
                            This can take 30–90 s on a cold start.
                        </p>
                        <button
                            onClick={() => window.location.reload()}
                            className="mt-1 text-xs underline text-primary hover:opacity-80"
                        >
                            Retry
                        </button>
                    </div>
                )}
            </div>
        );
    }

    return user ? <>{children}</> : null;
};

export default ProtectedRoute;
