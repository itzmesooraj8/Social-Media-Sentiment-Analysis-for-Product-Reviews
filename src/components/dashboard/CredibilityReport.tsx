import { motion } from 'framer-motion';
import { Shield, Bot, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';
import { CredibilityReport as CredibilityReportType } from '@/types/sentinel';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

interface CredibilityReportProps {
  report: CredibilityReportType;
  isLoading?: boolean;
}

export function CredibilityReport({ report, isLoading }: CredibilityReportProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="space-y-4">
          <div className="h-24 bg-muted/50 rounded-xl" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-muted/50 rounded-xl" />
            <div className="h-16 bg-muted/50 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  const scoreColor = report.overallScore >= 85 
    ? 'text-sentinel-positive' 
    : report.overallScore >= 70 
      ? 'text-sentinel-warning' 
      : 'text-sentinel-negative';

  const stats = [
    { 
      label: 'Verified Reviews', 
      value: report.verifiedReviews.toLocaleString(), 
      icon: CheckCircle,
      color: 'text-sentinel-positive'
    },
    { 
      label: 'Bots Detected', 
      value: report.botsDetected, 
      icon: Bot,
      color: 'text-sentinel-negative'
    },
    { 
      label: 'Spam Clusters', 
      value: report.spamClusters, 
      icon: AlertTriangle,
      color: 'text-sentinel-warning'
    },
    { 
      label: 'Suspicious', 
      value: report.suspiciousPatterns, 
      icon: BarChart3,
      color: 'text-sentinel-neutral'
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.9 }}
      className="glass-card p-6"
    >
      <div className="flex items-center gap-2 mb-6">
        <Shield className="h-5 w-5 text-sentinel-credibility" />
        <h3 className="text-lg font-semibold">Credibility Report</h3>
      </div>
      
      {/* Overall Score */}
      <div className="glass-card p-4 rounded-xl mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-muted-foreground">Overall Credibility Score</span>
          <motion.span 
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 1 }}
            className={cn('text-3xl font-bold', scoreColor)}
          >
            {report.overallScore.toFixed(1)}%
          </motion.span>
        </div>
        <Progress 
          value={report.overallScore} 
          className="h-2"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Analyzed {report.totalAnalyzed.toLocaleString()} reviews
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 1 + index * 0.1 }}
            className="glass-card p-3 rounded-xl"
          >
            <div className="flex items-center gap-2 mb-1">
              <stat.icon className={cn('h-4 w-4', stat.color)} />
              <span className="text-xs text-muted-foreground">{stat.label}</span>
            </div>
            <p className="text-xl font-semibold">{stat.value}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
