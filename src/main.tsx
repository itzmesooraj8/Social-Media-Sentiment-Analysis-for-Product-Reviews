import { StrictMode, Component } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Silent error boundary - redirects to home on error
class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean }> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: any, errorInfo: any) {
        // Log to console but don't show to user
        console.error("App Error:", error, errorInfo);
        // Reload the page to recover
        setTimeout(() => window.location.href = '/', 100);
    }

    render() {
        if (this.state.hasError) {
            // Show nothing while redirecting
            return <div style={{ background: '#0a0a0a', minHeight: '100vh' }} />;
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
