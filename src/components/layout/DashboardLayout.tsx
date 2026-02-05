import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X } from 'lucide-react';
import { AppSidebar } from './AppSidebar';
import { DashboardHeader } from './DashboardHeader';
import { getSystemStatus } from '@/lib/api';

interface DashboardLayoutProps {
  children: React.ReactNode;
  lastUpdated?: Date;
  isCrisis?: boolean;
}

export function DashboardLayout({ children, lastUpdated, isCrisis }: DashboardLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [missingIntegrations, setMissingIntegrations] = useState<string[]>([]);
  const [showBanner, setShowBanner] = useState(true);

  useEffect(() => {
    getSystemStatus().then((status) => {
      const missing = [];
      if (!status.reddit) missing.push("Reddit");
      if (!status.twitter) missing.push("Twitter");
      if (!status.youtube) missing.push("YouTube");

      if (missing.length > 0) {
        setMissingIntegrations(missing);
      }
    });
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <motion.div
        initial={false}
        animate={{
          marginLeft: sidebarCollapsed ? 72 : 280,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="flex flex-col min-h-screen"
      >
        <DashboardHeader lastUpdated={lastUpdated} isCrisis={isCrisis} />

        <main className="flex-1 p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <AnimatePresence>
              {showBanner && missingIntegrations.length > 0 && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mb-6 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 flex items-start gap-3"
                >
                  <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-yellow-500">Partial Integration Configured</h3>
                    <p className="text-sm text-yellow-500/90 mt-1">
                      API keys are missing for <strong>{missingIntegrations.join(", ")}</strong>.
                      <br />
                      The system will skip these sources but <span className="font-semibold underline">will continue to collect data</span> from your active integrations.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowBanner(false)}
                    className="text-yellow-500/50 hover:text-yellow-500"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {children}
          </motion.div>
        </main>
      </motion.div>
    </div>
  );
}
