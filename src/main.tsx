import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { Toaster } from "@/components/ui/toaster";
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ErrorBoundary>
            <App />
            <Toaster />
        </ErrorBoundary>
    </StrictMode>
);
