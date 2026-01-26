
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signIn } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { motion } from 'framer-motion';
import { Lock, Mail, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Try Custom Backend Login first (for Admin/Admin)
            // If username is email-like, try Supabase? 
            // User said "username/password: admin/admin".
            // We'll try custom login first.
            try {
                // Import dynamically to avoid circular dep issues in some frameworks, but here direct import is fine if added to api.ts
                const { apiLogin } = await import('@/lib/api');
                const data = await apiLogin(email, password); // email state holds 'admin'
                if (data.token) {
                    localStorage.setItem('access_token', data.token);
                    // Force reload or just navigate?
                    // Navigation might not update AuthContext.
                    // Ideally we update AuthContext, but for demo speed:
                    window.location.href = '/dashboard';
                    return;
                }
            } catch (backendError) {
                // connection refused or invalid creds?
                // Fallback to Supabase if backend refused
                // console.log("Backend auth failed, trying Supabase", backendError);
                const { error } = await signIn(email, password);
                if (error) throw error;
                navigate('/dashboard');
            }
        } catch (err: any) {
            setError(err.message || 'Failed to login');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/20 via-background to-background p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md"
            >
                <Card className="glass-card border-border/50">
                    <CardHeader className="space-y-1">
                        <CardTitle className="text-2xl font-bold text-center">Sentiment Beacon</CardTitle>
                        <CardDescription className="text-center">
                            Enter your credentials to access the dashboard
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="email"
                                        type="text"
                                        placeholder="username or email"
                                        className="pl-10"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder="••••••••"
                                        className="pl-10"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>

                            {error && (
                                <div className="p-3 text-sm text-red-500 bg-red-500/10 rounded-md border border-red-500/20">
                                    {error}
                                </div>
                            )}

                            <Button type="submit" className="w-full bg-sentinel-credibility hover:bg-sentinel-credibility/90" disabled={loading}>
                                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 'Sign In'}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex justify-center">
                        <p className="text-sm text-muted-foreground">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-primary hover:underline">
                                Register
                            </Link>
                        </p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
