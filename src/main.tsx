import { StrictMode, Component } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Error boundary - show fallback UI without forcibly redirecting
class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean; error?: any }> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false, error: undefined };
    }

    static getDerivedStateFromError(error: any) {
        return { hasError: true, error };
    }

    componentDidCatch(error: any, errorInfo: any) {
        // Log error details for debugging but do not auto-redirect
        console.error('App Error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
                    <div className="max-w-lg text-center p-6">
                        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
                        <p className="text-sm text-muted-foreground mb-4">An unexpected error occurred. Check the console for details.</p>
                        <div className="flex gap-2 justify-center">
                            <button
                                onClick={() => window.location.reload()}
                                className="px-4 py-2 bg-sentinel-credibility text-black rounded"
                            >Reload</button>
                            <button
                                onClick={() => this.setState({ hasError: false, error: undefined })}
                                className="px-4 py-2 border rounded"
                            >Dismiss</button>
                        </div>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    </StrictMode>
);
