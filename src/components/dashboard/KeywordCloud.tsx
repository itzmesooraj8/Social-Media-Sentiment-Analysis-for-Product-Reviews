import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { TopKeyword } from '@/types/sentinel';
import { cn } from '@/lib/utils';

interface KeywordCloudProps {
  keywords: TopKeyword[];
  isLoading?: boolean;
}

export function KeywordCloud({ keywords, isLoading }: KeywordCloudProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-32 bg-muted rounded mb-4" />
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
            <div key={i} className="h-8 w-20 bg-muted/50 rounded-full" />
          ))}
        </div>
      </div>
    );
  }

  const sentimentStyles = {
    positive: 'bg-sentinel-positive/10 text-sentinel-positive border-sentinel-positive/30 hover:bg-sentinel-positive/20',
    negative: 'bg-sentinel-negative/10 text-sentinel-negative border-sentinel-negative/30 hover:bg-sentinel-negative/20',
    neutral: 'bg-muted text-muted-foreground border-border hover:bg-accent',
  };

  const TrendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.8 }}
      className="glass-card p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Top Keywords</h3>
      
      <div className="flex flex-wrap gap-2">
        {keywords.map((keyword, index) => {
          const Icon = TrendIcon[keyword.trend];
          
          return (
            <motion.div
              key={keyword.word}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium',
                'border transition-all duration-200 cursor-pointer',
                sentimentStyles[keyword.sentiment]
              )}
            >
              <span>{keyword.word}</span>
              <span className="text-xs opacity-70">({keyword.count})</span>
              <Icon className="h-3 w-3" />
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
