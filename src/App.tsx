import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
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

const AppRoutes = () => {
  const location = useLocation();

  return (
    <Routes location={location} key={location.pathname}>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Index />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/reports" element={<Reports />} />
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/products" element={<Products />} />
      <Route path="/products/:id" element={<ProductDetails />} />
      <Route path="/integrations" element={<Integrations />} />
      <Route path="/competitors" element={<Competitors />} />
      <Route path="/help" element={<Help />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
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
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
