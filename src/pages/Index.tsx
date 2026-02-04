import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from "sonner";
import { FileText, BarChart3, MessageSquare, Shield, RefreshCw } from 'lucide-react';
import { useDashboardData } from '@/hooks/useDashboardData';
import { getProducts, getInsights, triggerScrape } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

// ... (existing helper function calls if any)


import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { AspectRadarChart } from '@/components/dashboard/AspectRadarChart';
import { AlertsPanel } from '@/components/dashboard/AlertsPanel';
import { PlatformChart } from '@/components/dashboard/PlatformChart';
import { ImageWordCloud } from '@/components/dashboard/ImageWordCloud';
import { CredibilityReport } from '@/components/dashboard/CredibilityReport';
import { LiveReviewAnalyzer } from '@/components/dashboard/LiveReviewAnalyzer';
import { ReviewFeed } from '@/components/dashboard/ReviewFeed';
import { EmotionWheel } from '@/components/dashboard/EmotionWheel';
import { InsightCard } from '@/components/dashboard/InsightCard';
import { TopicClusters } from '@/components/dashboard/TopicClusters';
import { DashboardControls } from '@/components/dashboard/DashboardControls';

const Index = () => {
  const [selectedProductId, setSelectedProductId] = useState<string | undefined>(undefined);
  const { data, isLoading } = useDashboardData(selectedProductId);
  const { data: products, isLoading: productsLoading } = useQuery({ queryKey: ['products'], queryFn: getProducts });
  const queryClient = useQueryClient();

  // Default to first product if none selected? Or keep global.
  // User wants "as per the products", so maybe global view is fine initially.

  const { data: insightsData, isLoading: insightsLoading } = useQuery({
    queryKey: ['insights', selectedProductId],
    queryFn: () => getInsights(selectedProductId),
    // Always enabled now to get global insights too if backend supports it
    enabled: true
  });

  const scrapeMutation = useMutation({
    mutationFn: triggerScrape,
    onSuccess: (data) => {
      toast.success("Live Analysis Started", {
        description: `Agents are now scraping fresh data for ${data?.product_name || 'the product'}.`
      });
      // Invalidate to refresh
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['dashboard-aggregated'] }), 2000);
    },
    onError: (err) => {
      toast.error("Analysis Failed", { description: "Could not start agents." });
    }
  });

  /* Live Analysis Handler */
  const handleLiveAnalysis = () => {
    if (selectedProductId) {
      // Single Product Mode
      scrapeMutation.mutate(selectedProductId);
    } else {
      // Global Mode: Scrape top 3 products to refresh the "Live Feed"
      if (products && products.length > 0) {
        toast.info("Starting Global Live Analysis", {
          description: "Initiating live agents for top active products..."
        });
        // Limit to 3 to prevent rate limits
        const topProducts = products.slice(0, 3);
        topProducts.forEach((p: any) => {
          // slight delay to stagger
          setTimeout(() => scrapeMutation.mutate(p.id), 100);
        });
      } else {
        toast.warning("No products found to analyze");
      }
    }
  };

  const apiMetrics = data?.data || {};
  const recentReviews = apiMetrics?.recentReviews || [];
  const rawPlatformBreakdown = apiMetrics?.platformBreakdown || [];
  const platformBreakdown = Array.isArray(rawPlatformBreakdown) ? rawPlatformBreakdown : [];

  const assembled = {
    metrics: {
      totalReviews: apiMetrics.totalReviews ?? 0,
      sentimentDelta: apiMetrics.sentimentDelta ? parseFloat(apiMetrics.sentimentDelta.toFixed(1)) : 0,
      botsDetected: apiMetrics.credibilityReport?.botsDetected ?? 0,
      averageCredibility: apiMetrics.averageCredibility ?? 0,
    },
    recentReviews,
    sentimentTrends: apiMetrics.sentimentTrends || [],
    aspectScores: apiMetrics.aspectScores || [],
    alerts: apiMetrics.alerts || [],
    platformBreakdown,
    topKeywords: apiMetrics.topKeywords || [],
    credibilityReport: apiMetrics.credibilityReport || {
      overallScore: 0,
      verifiedReviews: 0,
      botsDetected: 0,
      spamClusters: 0,
      suspiciousPatterns: 0,
      totalAnalyzed: 0,
    },
    emotions: apiMetrics.emotionBreakdown || apiMetrics.emotions || [], // Use backend aggregated breakdown
    lastUpdated: new Date()
  };
  const isLoadingLocal = isLoading;

  const { data: summaryResp, isLoading: summaryLoading } = useQuery({
    queryKey: ['reportSummary'], // Legacy key, unused really
    queryFn: async () => ({
      summary: null,
      recommendations: []
    }),
    enabled: false
  });

  // Crisis Alert Logic: Trigger if sentiment drops significantly
  const isCrisis = assembled.metrics.sentimentDelta <= -15;

  useEffect(() => { }, [isCrisis]);

  /* Error State Handling */
  if (data?.isError || (products === undefined && !productsLoading && !isLoadingLocal)) {
    return (
      <DashboardLayout lastUpdated={new Date()} isCrisis={false}>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
          <Shield className="h-16 w-16 text-muted-foreground opacity-50" />
          <h3 className="text-xl font-semibold">System Offline</h3>
          <p className="text-muted-foreground max-w-md">
            Unable to connect to Sentinel Engine. The backend service may be restarting or offline.
          </p>
          <button onClick={() => window.location.reload()} className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Retry Connection
          </button>
        </div>
      </DashboardLayout>
    );
  }

  if (isLoadingLocal || productsLoading) {
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

        {/* Page Title + Live Indicator + Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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



          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground mr-2 font-medium">
              Global Overview
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLiveAnalysis}
              disabled={scrapeMutation.isPending}
              title="Refresh Global Data (Scrape Top Products)"
              className={`gap-2 ${scrapeMutation.isPending ? "animate-pulse" : ""}`}
            >
              <RefreshCw className={`h-4 w-4 ${scrapeMutation.isPending ? 'animate-spin' : ''}`} />
              Live Refresh
            </Button>
          </div>
        </div>

        {/* Controls Row */}
        <DashboardControls />

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
            changeType={assembled?.metrics.sentimentDelta >= 0 ? 'positive' : 'negative'}
            icon={BarChart3}
            accentColor={assembled?.metrics.sentimentDelta >= 0 ? 'positive' : 'negative'}
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
          <InsightCard isLoading={isLoading || summaryLoading || insightsLoading} summary={summaryResp?.summary} recommendations={insightsData || []} />
        </div>



        {/* Review Feed & Emotions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ReviewFeed reviews={assembled?.recentReviews ?? []} />
          <EmotionWheel isLoading={isLoading} data={assembled.emotions} />
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
          <ImageWordCloud
            productId={selectedProductId}
          />

          <CredibilityReport
            report={assembled.credibilityReport}
            isLoading={isLoadingLocal}
          />
        </div>
      </div>
    </DashboardLayout >
  );
};

export default Index;
