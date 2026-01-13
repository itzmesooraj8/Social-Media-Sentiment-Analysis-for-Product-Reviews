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

const insights: Insight[] = [
  {
    id: '1',
    type: 'trend',
    title: 'Positive Sentiment Surge',
    description: 'Positive reviews increased by 23% this week, primarily driven by recent product improvements.',
    metric: '+23%',
    change: 23,
  },
  {
    id: '2',
    type: 'alert',
    title: 'Shipping Complaints Detected',
    description: '45% more mentions of shipping delays compared to last month. Consider investigating logistics.',
    metric: '+45%',
    change: -45,
    actionLabel: 'View Details',
  },
  {
    id: '3',
    type: 'recommendation',
    title: 'Respond to Reddit Thread',
    description: 'A popular Reddit post with 500+ upvotes has questions about your product. Engaging could boost sentiment.',
    actionLabel: 'View Thread',
  },
  {
    id: '4',
    type: 'achievement',
    title: 'Credibility Score Milestone',
    description: 'Your average credibility score has exceeded 85% for the first time this quarter!',
    metric: '85%+',
  },
];

const insightConfig = {
  trend: {
    icon: TrendingUp,
    color: 'text-sentinel-credibility',
    bg: 'bg-sentinel-credibility/10',
    border: 'border-sentinel-credibility/30',
  },
  alert: {
    icon: AlertTriangle,
    color: 'text-sentinel-warning',
    bg: 'bg-sentinel-warning/10',
    border: 'border-sentinel-warning/30',
  },
  recommendation: {
    icon: Lightbulb,
    color: 'text-purple-400',
    bg: 'bg-purple-400/10',
    border: 'border-purple-400/30',
  },
  achievement: {
    icon: CheckCircle,
    color: 'text-sentinel-positive',
    bg: 'bg-sentinel-positive/10',
    border: 'border-sentinel-positive/30',
  },
};

interface InsightCardProps {
  isLoading?: boolean;
}

export function InsightCard({ isLoading }: InsightCardProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-32 bg-muted rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-muted/50 rounded-lg" />
          ))}
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
        {insights.map((insight, index) => {
          const config = insightConfig[insight.type];
          const Icon = config.icon;
          
          return (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={cn(
                'p-4 rounded-lg border bg-background/50',
                config.border
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('p-2 rounded-lg flex-shrink-0', config.bg)}>
                  <Icon className={cn('h-4 w-4', config.color)} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm">{insight.title}</h4>
                    {insight.metric && (
                      <span className={cn(
                        'text-sm font-bold',
                        insight.change && insight.change > 0 ? 'text-sentinel-positive' : 
                        insight.change && insight.change < 0 ? 'text-sentinel-negative' : 'text-sentinel-credibility'
                      )}>
                        {insight.metric}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {insight.description}
                  </p>
                  
                  {insight.actionLabel && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className={cn('mt-2 h-7 px-2 text-xs', config.color)}
                    >
                      {insight.actionLabel}
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <Button variant="outline" className="w-full mt-4" size="sm">
        View All Insights
        <ArrowRight className="h-4 w-4 ml-2" />
      </Button>
    </motion.div>
  );
}
