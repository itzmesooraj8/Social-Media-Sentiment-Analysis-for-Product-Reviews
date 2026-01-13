import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { 
  AlertTriangle, 
  Bot, 
  TrendingDown, 
  Zap, 
  ShieldAlert,
  ExternalLink
} from 'lucide-react';
import { Alert, AlertSeverity, AlertType } from '@/types/sentinel';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';

interface AlertsPanelProps {
  alerts: Alert[];
  isLoading?: boolean;
}

const alertIcons: Record<AlertType, typeof AlertTriangle> = {
  bot_detected: Bot,
  spam_cluster: ShieldAlert,
  review_surge: Zap,
  sentiment_shift: TrendingDown,
  fake_review: AlertTriangle,
};

const severityStyles: Record<AlertSeverity, string> = {
  low: 'border-l-sentinel-neutral bg-sentinel-neutral/5',
  medium: 'border-l-sentinel-warning bg-sentinel-warning/5',
  high: 'border-l-sentinel-negative bg-sentinel-negative/5',
  critical: 'border-l-sentinel-negative bg-sentinel-negative/10 animate-pulse-glow',
};

const severityBadgeStyles: Record<AlertSeverity, string> = {
  low: 'bg-sentinel-neutral/20 text-sentinel-neutral',
  medium: 'bg-sentinel-warning/20 text-sentinel-warning',
  high: 'bg-sentinel-negative/20 text-sentinel-negative',
  critical: 'bg-sentinel-negative/30 text-sentinel-negative',
};

export function AlertsPanel({ alerts, isLoading }: AlertsPanelProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-[350px] animate-pulse">
        <div className="h-6 w-32 bg-muted rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 bg-muted/50 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
      className="glass-card p-6 h-[350px] flex flex-col"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Recent Alerts</h3>
        <span className="text-xs text-muted-foreground glass-card px-2 py-1 rounded-full">
          {alerts.length} active
        </span>
      </div>
      
      <ScrollArea className="flex-1 -mx-2 px-2">
        <div className="space-y-3">
          {alerts.map((alert, index) => {
            const Icon = alertIcons[alert.type];
            
            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={cn(
                  'p-4 rounded-xl border-l-4 transition-all duration-200',
                  'hover:translate-x-1 cursor-pointer group',
                  severityStyles[alert.severity]
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'p-2 rounded-lg',
                    severityBadgeStyles[alert.severity]
                  )}>
                    <Icon className="h-4 w-4" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn(
                        'text-xs font-medium px-2 py-0.5 rounded-full uppercase tracking-wider',
                        severityBadgeStyles[alert.severity]
                      )}>
                        {alert.severity}
                      </span>
                      {alert.metadata?.platform && (
                        <span className="text-xs text-muted-foreground capitalize">
                          {alert.metadata.platform}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-foreground line-clamp-2 mb-1">
                      {alert.message}
                    </p>
                    
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(alert.timestamp, { addSuffix: true })}
                    </p>
                  </div>
                  
                  <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </motion.div>
            );
          })}
        </div>
      </ScrollArea>
    </motion.div>
  );
}
