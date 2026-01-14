import { useEffect } from 'react';
import { toast } from "sonner";
import { FileText, BarChart3, MessageSquare, Shield } from 'lucide-react';
import { useDashboardData } from '@/hooks/useDashboardData';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { AspectRadarChart } from '@/components/dashboard/AspectRadarChart';
import { AlertsPanel } from '@/components/dashboard/AlertsPanel';
import { SentimentDistribution } from '@/components/dashboard/SentimentDistribution';
import { PlatformChart } from '@/components/dashboard/PlatformChart';
import { KeywordCloud } from '@/components/dashboard/KeywordCloud';
import { CredibilityReport } from '@/components/dashboard/CredibilityReport';
import { LiveReviewAnalyzer } from '@/components/dashboard/LiveReviewAnalyzer';
import { ReviewFeed } from '@/components/dashboard/ReviewFeed';
import { EmotionWheel } from '@/components/dashboard/EmotionWheel';
import { InsightCard } from '@/components/dashboard/InsightCard';
import { TopicClusters } from '@/components/dashboard/TopicClusters';
import { DateRangePicker } from '@/components/dashboard/DateRangePicker';
import { ExportButton } from '@/components/dashboard/ExportButton';

const Index = () => {
  const { data, isLoading } = useDashboardData();

  // Pulse Logic: If last 5 reviews are ALL negative, trigger crisis mode
  const recentReviews = data?.recentReviews || [];
  const isCrisis = recentReviews.length >= 5 && recentReviews.slice(0, 5).every(r => r.sentiment === 'negative');

  useEffect(() => {
    if (isCrisis) {
      toast.error("CRISIS ALERT: Negative Sentiment Spike Detected!", {
        description: "The last 5 reviews were negative. Use the War Room to investigate.",
        duration: 8000,
      });
    }
  }, [isCrisis]);

  return (
    <DashboardLayout lastUpdated={data?.lastUpdated} isCrisis={isCrisis}>
      <div className="space-y-6">
        {/* Controls Row */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <DateRangePicker />
          <ExportButton />
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Reviews Processed"
            value={data?.metrics.totalReviews ?? 0}
            icon={FileText}
            accentColor="positive"
            delay={0}
            subtitle="Last 30 days"
          />
          <MetricCard
            title="Sentiment Delta"
            value={data?.metrics.sentimentDelta ?? 0}
            change={data?.metrics.sentimentDelta}
            changeType={data?.metrics.sentimentDelta && data.metrics.sentimentDelta > 0 ? 'positive' : 'negative'}
            icon={BarChart3}
            accentColor={data?.metrics.sentimentDelta && data.metrics.sentimentDelta > 0 ? 'positive' : 'negative'}
            delay={1}
            suffix="%"
            subtitle="vs last week"
          />
          <MetricCard
            title="Bots Detected"
            value={data?.metrics.botsDetected ?? 0}
            icon={MessageSquare}
            accentColor="negative"
            delay={2}
            subtitle="Flagged for review"
          />
          <MetricCard
            title="Credibility Score"
            value={data?.metrics.averageCredibility?.toFixed(1) ?? '0'}
            icon={Shield}
            accentColor="credibility"
            delay={3}
            suffix="%"
            subtitle="Verified authentic"
          />
        </div>

        {/* Live Analyzer & Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LiveReviewAnalyzer />
          <InsightCard isLoading={isLoading} />
        </div>

        {/* Sentiment Trend Chart */}
        <SentimentTrendChart
          data={data?.sentimentTrends ?? []}
          isLoading={isLoading}
        />

        {/* Review Feed & Emotions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ReviewFeed reviews={data?.recentReviews} />
          <EmotionWheel isLoading={isLoading} />
        </div>

        {/* Aspect Analysis & Alerts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AspectRadarChart
            data={data?.aspectScores ?? []}
            isLoading={isLoading}
          />
          <AlertsPanel
            alerts={data?.alerts ?? []}
            isLoading={isLoading}
          />
        </div>

        {/* Topics & Platform Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopicClusters isLoading={isLoading} />
          <PlatformChart
            data={data?.platformBreakdown ?? []}
            isLoading={isLoading}
          />
        </div>

        {/* Keywords & Credibility Report */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <KeywordCloud
            keywords={data?.topKeywords ?? []}
            isLoading={isLoading}
          />
          <CredibilityReport
            report={data?.credibilityReport ?? {
              overallScore: 0,
              botsDetected: 0,
              spamClusters: 0,
              suspiciousPatterns: 0,
              verifiedReviews: 0,
              totalAnalyzed: 0,
            }}
            isLoading={isLoading}
          />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Index;
