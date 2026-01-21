import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { toast } from "sonner";
import { FileText, BarChart3, MessageSquare, Shield } from 'lucide-react';
import { useRealtimeDashboard } from '@/hooks/useDashboardData';
import { Skeleton } from '@/components/ui/skeleton';
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
  const { data, isLoading, refetch } = useRealtimeDashboard();

  const apiMetrics = data?.metrics || {};
  const recentReviews = data?.recentReviews || [];
  const rawPlatformBreakdown = data?.platformBreakdown || {};
  const platformBreakdown = Array.isArray(rawPlatformBreakdown)
    ? rawPlatformBreakdown
    : Object.entries(rawPlatformBreakdown || {}).map(([platform, vals]) => ({ platform, ...(vals as any) }));

  const assembled = {
    metrics: {
      totalReviews: apiMetrics.totalReviews ?? 0,
      sentimentDelta: apiMetrics.sentimentDelta ?? 0,
      botsDetected: apiMetrics.botsDetected ?? 0,
      averageCredibility: apiMetrics.averageCredibility ?? 0,
    },
    recentReviews,
    sentimentTrends: [],
    aspectScores: [],
    alerts: [],
    platformBreakdown,
    topKeywords: [],
    credibilityReport: {},
    lastUpdated: new Date()
  };
  const isLoadingLocal = isLoading;

  const { data: summaryResp, isLoading: summaryLoading } = useQuery({
    queryKey: ['reportSummary'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/dashboard');
      if (!response.ok) throw new Error('Failed to fetch summary');
      const json = await response.json();
      // Only show real AI summary, no fallback text
      return {
        summary: json.data?.aiSummary || null
      };
    },
    retry: false
  });

  // Pulse Logic: If last 5 reviews are ALL negative, trigger crisis mode
  const isCrisis = (assembled?.recentReviews || []).length >= 5 && (assembled.recentReviews || []).slice(0, 5).every(r => (r.sentiment || r.sentiment_label || '').toLowerCase() === 'negative');

  useEffect(() => {
    if (isCrisis) {
      toast.error("CRISIS ALERT: Negative Sentiment Spike Detected!", {
        description: "The last 5 reviews were negative. Use the War Room to investigate.",
        duration: 8000,
      });
    }
  }, [isCrisis]);

  if (isLoadingLocal) {
    return (
      <DashboardLayout lastUpdated={new Date()} isCrisis={false}>
        <div className="p-6">
          <Skeleton className="h-6 w-48 mb-4" />
          <Skeleton className="h-40 w-full" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout lastUpdated={assembled?.lastUpdated} isCrisis={isCrisis}>
      <div className="space-y-6">

        {/* Page Title + Live Indicator */}
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">Dashboard</h2>
          <div className="flex items-center gap-2 glass-card px-2 py-1 rounded-full">
            <div className="relative flex items-center justify-center">
              <span className="absolute h-2.5 w-2.5 rounded-full bg-sentinel-positive animate-ping opacity-70" />
              <span className="relative h-2 w-2 rounded-full bg-sentinel-positive" />
            </div>
            <span className="text-sm font-medium text-sentinel-positive">Live Data Feed</span>
          </div>
        </div>

        {/* Controls Row */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <DateRangePicker />
          <ExportButton />
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Reviews Processed"
            value={assembled?.metrics.totalReviews ?? 0}
            icon={FileText}
            accentColor="positive"
            delay={0}
            subtitle="Last 30 days"
          />
          <MetricCard
            title="Sentiment Delta"
            value={assembled?.metrics.sentimentDelta ?? 0}
            change={assembled?.metrics.sentimentDelta}
            changeType={assembled?.metrics.sentimentDelta && assembled.metrics.sentimentDelta > 0 ? 'positive' : 'negative'}
            icon={BarChart3}
            accentColor={assembled?.metrics.sentimentDelta && assembled.metrics.sentimentDelta > 0 ? 'positive' : 'negative'}
            delay={1}
            suffix="%"
            subtitle="vs last week"
          />
          <MetricCard
            title="Bots Detected"
            value={assembled?.metrics.botsDetected ?? 0}
            icon={MessageSquare}
            accentColor="negative"
            delay={2}
            subtitle="Flagged for review"
          />
          <MetricCard
            title="Credibility Score"
            value={assembled?.metrics.averageCredibility?.toFixed(1) ?? '0'}
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
          <InsightCard isLoading={isLoading || summaryLoading} summary={summaryResp?.summary} />
        </div>

        {/* Sentiment Trend Chart */}
        <SentimentTrendChart
          data={assembled?.sentimentTrends ?? []}
          isLoading={isLoadingLocal}
        />

        {/* Review Feed & Emotions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ReviewFeed reviews={assembled?.recentReviews ?? []} />
          <EmotionWheel isLoading={isLoading} />
        </div>

        {/* Aspect Analysis & Alerts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AspectRadarChart
            data={assembled?.aspectScores ?? []}
            isLoading={isLoadingLocal}
          />
          <AlertsPanel
            alerts={assembled?.alerts ?? []}
            isLoading={isLoadingLocal}
          />
        </div>

        {/* Topics & Platform Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopicClusters isLoading={isLoading} />
          <PlatformChart
            data={assembled?.platformBreakdown ?? []}
            isLoading={isLoadingLocal}
          />
        </div>

        {/* Keywords & Credibility Report */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <KeywordCloud
            keywords={assembled?.topKeywords ?? []}
            isLoading={isLoadingLocal}
          />


          <CredibilityReport
            report={assembled?.credibilityReport && Object.keys(assembled.credibilityReport || {}).length > 0 ? assembled.credibilityReport : {
              overallScore: 0,
              verifiedReviews: 0,
              botsDetected: 0,
              spamClusters: 0,
              suspiciousPatterns: 0,
              totalAnalyzed: 0,
            }}
            isLoading={isLoadingLocal}
          />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Index;
