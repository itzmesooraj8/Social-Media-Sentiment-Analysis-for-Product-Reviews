import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/components/ThemeProvider";
import { useEffect } from "react";
import Index from "./pages/Index";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";
import Products from "./pages/Products";
import ProductDetails from "./pages/ProductDetails";
import Integrations from "./pages/Integrations";
import Competitors from "./pages/Competitors";
import Help from "./pages/Help";

import ProtectedRoute from "@/components/auth/ProtectedRoute";
import { AuthProvider } from "@/context/AuthContext";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

// Ping the backend on app startup so Render free-tier wakes up before the user
// tries to do anything. Fire-and-forget; failures are silently ignored.
const pingBackend = () => {
  const backendUrl = (import.meta.env.VITE_API_URL || 'https://social-media-sentiment-analysis-for.onrender.com')
    .replace(/\/api$/, '');
  fetch(`${backendUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(60000) })
    .then(() => console.log('[Sentinel] Backend is awake ✓'))
    .catch(() => console.warn('[Sentinel] Backend wake-up ping failed – will retry on first request'));
};

const App = () => {
  // Wake up the Render backend as early as possible
  useEffect(() => { pingBackend(); }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="sentinel-ui-theme">
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/auth" element={<LoginPage />} /> {/* Backwards compatibility or redirect */}

                <Route path="/help" element={<Help />} />

                {/* Protected Routes */}
                <Route path="/" element={<ProtectedRoute><Index /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><Index /></ProtectedRoute>} />
                <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
                <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
                <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
                <Route path="/products" element={<ProtectedRoute><Products /></ProtectedRoute>} />
                <Route path="/products/:id" element={<ProtectedRoute><ProductDetails /></ProtectedRoute>} />
                <Route path="/integrations" element={<ProtectedRoute><Integrations /></ProtectedRoute>} />
                <Route path="/competitors" element={<ProtectedRoute><Competitors /></ProtectedRoute>} />


                <Route path="*" element={<ProtectedRoute><Index /></ProtectedRoute>} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
