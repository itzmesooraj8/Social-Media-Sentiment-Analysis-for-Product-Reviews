import { motion } from 'framer-motion';
import { Activity, Clock } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { format } from 'date-fns';
import { UserNav } from '@/components/common/UserNav';

interface DashboardHeaderProps {
  lastUpdated?: Date;
  isCrisis?: boolean;
}

export function DashboardHeader({ lastUpdated, isCrisis = false }: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-30 glass-card rounded-none border-b border-border/50 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Title Section */}
        <div className="flex items-center gap-4">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-2xl font-bold tracking-tight"
          >
            <span className="gradient-text">Sentinel Engine</span>
          </motion.h1>

          {/* Live Indicator */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="flex items-center gap-2 glass-card px-3 py-1.5 rounded-full"
          >
            <div className="relative flex items-center justify-center">
              <span className={`absolute h-2.5 w-2.5 rounded-full ${isCrisis ? 'bg-sentinel-negative animate-ping duration-300' : 'bg-sentinel-positive animate-ping'} opacity-75`} />
              <span className={`relative h-2 w-2 rounded-full ${isCrisis ? 'bg-sentinel-negative' : 'bg-sentinel-positive'}`} />
            </div>
            <span className={`text-xs font-semibold uppercase tracking-wider ${isCrisis ? 'text-sentinel-negative' : 'text-sentinel-positive'}`}>
              {isCrisis ? 'CRISIS DETECTED' : 'LIVE SYSTEM'}
            </span>
          </motion.div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          {/* Last Updated */}
          {lastUpdated && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="hidden md:flex items-center gap-2 text-sm text-muted-foreground"
            >
              <Clock className="h-4 w-4" />
              <span>Updated {format(lastUpdated, 'HH:mm:ss')}</span>
            </motion.div>
          )}

          {/* Activity Indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
            className="hidden sm:flex items-center gap-2 glass-card px-3 py-1.5 rounded-lg"
          >
            <Activity className="h-4 w-4 text-sentinel-positive animate-pulse" />
            <span className="text-xs font-medium">Processing</span>
          </motion.div>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Nav */}
          <UserNav />
        </div>
      </div>
    </header>
  );
}
