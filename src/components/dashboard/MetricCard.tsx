import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  subtitle?: string;
  icon: LucideIcon;
  accentColor: 'positive' | 'negative' | 'credibility' | 'neutral';
  delay?: number;
  prefix?: string;
  suffix?: string;
  animate?: boolean;
}

export function MetricCard({
  title,
  value,
  change,
  changeType = 'neutral',
  subtitle,
  icon: Icon,
  accentColor,
  delay = 0,
  prefix = '',
  suffix = '',
  animate = true,
}: MetricCardProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const hasAnimated = useRef(false);

  // Animated counter effect
  useEffect(() => {
    if (!animate || hasAnimated.current) return;
    if (typeof value !== 'number') {
      hasAnimated.current = true;
      return;
    }

    hasAnimated.current = true;
    // Disabled animation to prevent auto-refresh
    setDisplayValue(value);

    // Original animation code (disabled):
    // const timer = setInterval(() => {
    //   setDisplayValue((prev) => {
    //     const diff = value - prev;
    //     if (Math.abs(diff) < 1) return value;
    //     return prev + diff * 0.1;
    //   });
    // }, 50);
    // return () => clearInterval(timer);
  }, [value]);

  const accentClasses = {
    positive: 'accent-line-positive',
    negative: 'accent-line-negative',
    credibility: 'accent-line-credibility',
    neutral: '',
  };

  const iconBgClasses = {
    positive: 'bg-sentinel-positive/10 text-sentinel-positive',
    negative: 'bg-sentinel-negative/10 text-sentinel-negative',
    credibility: 'bg-sentinel-credibility/10 text-sentinel-credibility',
    neutral: 'bg-muted text-muted-foreground',
  };

  const ChangeIcon = changeType === 'positive' ? TrendingUp : changeType === 'negative' ? TrendingDown : Minus;
  const changeColorClass = changeType === 'positive' ? 'text-sentinel-positive' : changeType === 'negative' ? 'text-sentinel-negative' : 'text-muted-foreground';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: delay * 0.1 }}
      className="glass-card-hover p-6 relative overflow-hidden group"
    >
      {/* Accent Line */}
      <div className={accentClasses[accentColor]} />

      {/* Content */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>

          <div className="flex items-baseline gap-1">
            <motion.span
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: delay * 0.1 + 0.2 }}
              className="text-3xl font-bold tracking-tight"
            >
              {prefix}
              {typeof value === 'number' ? displayValue.toLocaleString() : value}
              {suffix}
            </motion.span>
          </div>

          {/* Change Indicator */}
          {change !== undefined && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: delay * 0.1 + 0.4 }}
              className={cn('flex items-center gap-1 mt-2', changeColorClass)}
            >
              <ChangeIcon className="h-4 w-4" />
              <span className="text-sm font-medium">
                {change > 0 ? '+' : ''}{change}%
              </span>
              {subtitle && (
                <span className="text-xs text-muted-foreground ml-1">{subtitle}</span>
              )}
            </motion.div>
          )}

          {!change && subtitle && (
            <p className="text-xs text-muted-foreground mt-2">{subtitle}</p>
          )}
        </div>

        {/* Icon */}
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: delay * 0.1 + 0.3, type: 'spring' }}
          className={cn(
            'p-3 rounded-xl transition-transform duration-300 group-hover:scale-110',
            iconBgClasses[accentColor]
          )}
        >
          <Icon className="h-5 w-5" />
        </motion.div>
      </div>
    </motion.div>
  );
}
