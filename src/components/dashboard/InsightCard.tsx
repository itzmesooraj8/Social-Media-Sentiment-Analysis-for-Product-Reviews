import { motion } from 'framer-motion';
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface Insight {
  id: string;
  type: 'trend' | 'alert' | 'recommendation' | 'achievement';
  title: string;
  description: string;
  metric?: string;
  change?: number;
  actionLabel?: string;
}

const insightConfig = {
  recommendation: {
    icon: Lightbulb,
    color: 'text-purple-400',
    bg: 'bg-purple-400/10',
    border: 'border-purple-400/30',
  }
};

interface InsightCardProps {
  isLoading?: boolean;
  summary?: string;
}

export function InsightCard({ isLoading, summary }: InsightCardProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-32 bg-muted rounded mb-4" />
        <div className="space-y-3">
          <div className="h-24 bg-muted/50 rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="glass-card p-6"
    >
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="h-5 w-5 text-sentinel-credibility" />
        <h3 className="text-lg font-semibold">Smart Insights</h3>
      </div>
      <p className="text-sm text-muted-foreground mb-4">AI-generated analysis and recommendations</p>

      <div className="space-y-3">
        {summary ? (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={cn('p-4 rounded-lg border bg-background/50', insightConfig.recommendation.border)}
          >
            <div className="flex items-start gap-3">
              <div className={cn('p-2 rounded-lg flex-shrink-0', insightConfig.recommendation.bg)}>
                <Lightbulb className={cn('h-4 w-4', insightConfig.recommendation.color)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium text-sm">Smart Summary</h4>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{summary}</p>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="text-center p-4 text-muted-foreground text-sm">
            No insights generated yet.
          </div>
        )}
      </div>

      <Button variant="outline" className="w-full mt-4" size="sm">
        View All Insights
        <ArrowRight className="h-4 w-4 ml-2" />
      </Button>
    </motion.div>
  );
}


