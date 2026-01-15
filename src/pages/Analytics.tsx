
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Skeleton } from '@/components/ui/skeleton';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Activity,
  Target,
  Zap,
  Globe
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useDashboardData } from '@/hooks/useDashboardData';
import { getAnalytics, getExecutiveSummary } from '@/lib/api';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  ComposedChart,
  Line,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const Analytics = () => {
  const navigate = useNavigate();

  // 1. Fetch Real Data via Hooks (TanStack Query)
  const { data: dashboardData, isLoading: isDashboardLoading } = useDashboardData();

  const {
    data: analyticsRes,
    isLoading: isAnalyticsLoading,
    error: analyticsError
  } = useQuery({
    queryKey: ['analytics'],
    queryFn: getAnalytics,
    retry: 1,
  });

  const {
    data: summaryRes,
    isLoading: isSummaryLoading
  } = useQuery({
    queryKey: ['executiveSummary'],
    queryFn: getExecutiveSummary,
    retry: 1
  });

  // 2. Global Loading State
  const loading = isDashboardLoading || isAnalyticsLoading || isSummaryLoading;

  // 3. Error Handling (Auth Redirect)
  useEffect(() => {
    if (analyticsError) {
      // @ts-ignore
      if (analyticsError.status === 401 || analyticsError.message?.includes('401')) {
        navigate('/login');
      }
    }
  }, [analyticsError, navigate]);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6 p-6">
          <Skeleton className="h-12 w-1/3 mb-6" />
          <Skeleton className="h-24 w-full mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32 w-full" />)}
          </div>
          <Skeleton className="h-[400px] w-full" />
        </div>
      </DashboardLayout>
    );
  }

  // 4. Data Transformation (Strictly No Mocks)
  const analyticsData = analyticsRes?.success ? analyticsRes.data : null;
  const metrics = dashboardData?.metrics || {};
  const sentimentRows = analyticsData?.sentimentData || []; // Raw rows for correlation
  const platformBreakdown = analyticsData?.platformBreakdown || {};

  // KPI Stats - From DB
  const stats = [
    {
      label: 'Avg Response Time',
      value: metrics.processingSpeed ? `${metrics.processingSpeed}ms` : 'N/A',
      change: 0, // Delta not yet in DB
      icon: Zap,
      color: 'text-sentinel-positive'
    },
    {
      label: 'Engagement Rate',
      value: metrics.engagementRate ? `${(metrics.engagementRate * 100).toFixed(1)}%` : '0%',
      change: 0,
      icon: Target,
      color: 'text-sentinel-credibility'
    },
    {
      label: 'Model Accuracy',
      value: metrics.modelAccuracy ? `${(metrics.modelAccuracy * 100).toFixed(1)}%` : '0%',
      change: 0,
      icon: Activity,
      color: 'text-sentinel-positive'
    },
    {
      label: 'Total Reach',
      value: metrics.totalReach ? metrics.totalReach.toLocaleString() : '0',
      change: 0,
      icon: Globe,
      color: 'text-sentinel-credibility'
    },
  ];

  // AI Summary
  const aiSummary = summaryRes?.success ? summaryRes.summary : "No sufficient data to generate summary.";

  // Chart 1: Sentiment Trends (Daily)
  const sentimentTrends = dashboardData?.sentimentTrends || [];

  // Chart 2: Hourly Engagement (Real)
  const engagementMap = new Array(24).fill(0);
  sentimentRows.forEach((row: any) => {
    if (row.created_at) {
      const h = new Date(row.created_at).getHours();
      engagementMap[h]++;
    }
  });
  const engagementData = engagementMap.map((count, hour) => ({
    hour: `${hour}:00`,
    engagement: count
  }));

  // Chart 3: Platform Breakdown (Real)
  // Calculate global sentiment ratios first
  const globalPos = sentimentRows.filter((r: any) => r.label === 'POSITIVE').length;
  const globalNeg = sentimentRows.filter((r: any) => r.label === 'NEGATIVE').length;
  const globalNeu = sentimentRows.filter((r: any) => r.label === 'NEUTRAL').length;
  const globalTotal = (globalPos + globalNeg + globalNeu) || 1;

  const platformPerformanceChart = Object.entries(platformBreakdown).map(([platform, count]: [string, any]) => ({
    platform,
    total: Number(count),
    positive: Math.round((globalPos / globalTotal) * 100),
    neutral: Math.round((globalNeu / globalTotal) * 100),
    negative: Math.round((globalNeg / globalTotal) * 100)
  })).sort((a, b) => b.total - a.total);

  // Chart 4: Correlation (Score vs Credibility)
  const correlationData = sentimentRows.map((row: any) => ({
    sentiment: row.score ? Math.round(row.score * 100) : 50,
    engagement: Math.round(row.credibility || 0),
    volume: 100
  })).slice(0, 100); // Max 100 points

  // Empty State Check (Only if truly empty and not just loading)
  if (!analyticsData || (sentimentRows.length === 0 && !metrics.totalReviews)) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4">
          <div className="p-4 rounded-full bg-muted">
            <BarChart3 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold">No Analytics Data Yet</h2>
          <p className="text-muted-foreground max-w-sm">
            Import a dataset or scrape reviews to see real-time insights here.
          </p>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Page Header */}
        <motion.div variants={itemVariants}>
          <h1 className="text-2xl font-bold">Advanced Analytics</h1>
          <p className="text-muted-foreground">Deep dive into sentiment patterns and trends</p>
        </motion.div>

        {/* AI Executive Summary */}
        <motion.div variants={itemVariants}>
          <Card className="glass-card border-sentinel-credibility/50 bg-sentinel-credibility/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="h-5 w-5 text-sentinel-credibility" />
                AI Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm leading-relaxed whitespace-pre-line">
                {aiSummary}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* KPI Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <Card key={stat.label} className="glass-card border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-2xl font-bold mt-1">{stat.value}</p>
                    <div className="flex items-center gap-1 mt-1">
                      {stat.change > 0 ? (
                        <TrendingUp className="h-3 w-3 text-sentinel-positive" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-sentinel-negative" />
                      )}
                      <span className={stat.change > 0 ? 'text-sentinel-positive text-xs' : 'text-sentinel-negative text-xs'}>
                        {Math.abs(stat.change)}%
                      </span>
                    </div>
                  </div>
                  <stat.icon className={`h-8 w-8 ${stat.color} opacity-50`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>

        {/* Analytics Tabs */}
        <motion.div variants={itemVariants}>
          <Tabs defaultValue="trends" className="space-y-4">
            <TabsList className="glass-card border-border/50">
              <TabsTrigger value="trends">Trends</TabsTrigger>
              <TabsTrigger value="comparison">Hourly</TabsTrigger>
              <TabsTrigger value="correlation">Correlation</TabsTrigger>
              <TabsTrigger value="platforms">Platforms</TabsTrigger>
            </TabsList>

            <TabsContent value="trends">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Daily Trend */}
                <Card className="glass-card border-border/50">
                  <CardHeader><CardTitle>Daily Sentiment Volume</CardTitle></CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={sentimentTrends}>
                          <defs>
                            <linearGradient id="positiveGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="hsl(var(--sentinel-positive))" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="hsl(var(--sentinel-positive))" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="negativeGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="hsl(var(--sentinel-negative))" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="hsl(var(--sentinel-negative))" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                          <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--card))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px'
                            }}
                          />
                          <Area type="monotone" dataKey="positive" stroke="hsl(var(--sentinel-positive))" fill="url(#positiveGradient)" strokeWidth={2} />
                          <Area type="monotone" dataKey="negative" stroke="hsl(var(--sentinel-negative))" fill="url(#negativeGradient)" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Hourly Engagement */}
                <Card className="glass-card border-border/50">
                  <CardHeader><CardTitle>Hourly Activity (UTC)</CardTitle></CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={engagementData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="hour" fontSize={12} stroke="#888" />
                          <YAxis fontSize={12} stroke="#888" />
                          <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ background: '#111', border: '1px solid #333' }} />
                          <Bar dataKey="engagement" fill="hsl(var(--sentinel-credibility))" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="comparison">
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-sentinel-credibility" />
                    Real-Time Sentiment Trend (Hourly)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      {
                        (() => {
                          const now = new Date();
                          const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                          const recent = (sentimentRows || []).filter((r: any) => r.created_at && new Date(r.created_at) >= dayAgo);

                          const buckets: Record<string, { sum: number; count: number }> = {};
                          recent.forEach((r: any) => {
                            const dt = new Date(r.created_at);
                            const label = dt.getHours().toString().padStart(2, '0') + ':00';
                            const score = (typeof r.score === 'number') ? (r.score * 100) : (r.score ? Number(r.score) : 0);
                            if (!buckets[label]) buckets[label] = { sum: 0, count: 0 };
                            buckets[label].sum += score;
                            buckets[label].count += 1;
                          });

                          const hourlyData = [] as any[];
                          for (let i = 0; i < 24; i++) {
                            const dt = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000);
                            const label = dt.getHours().toString().padStart(2, '0') + ':00';
                            const b = buckets[label];
                            hourlyData.push({ hour: label, avgSentiment: b && b.count ? (b.sum / b.count) : null, count: b ? b.count : 0 });
                          }

                          return (
                            <ComposedChart data={hourlyData}>
                              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                              <XAxis dataKey="hour" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: 'hsl(var(--card))',
                                  border: '1px solid hsl(var(--border))',
                                  borderRadius: '8px'
                                }}
                              />
                              <Legend />
                              <Line type="monotone" dataKey="avgSentiment" name="Avg Sentiment (0-100)" stroke="hsl(var(--sentinel-credibility))" strokeWidth={2} dot={{ r: 2 }} connectNulls={false} />
                            </ComposedChart>
                          );
                        })()
                      }
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="correlation">
              <Card className="glass-card border-border/50">
                <CardHeader><CardTitle>Confidence vs Credibility</CardTitle></CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                        <XAxis type="number" dataKey="sentiment" name="Confidence" unit="%" fontSize={12} stroke="#888" />
                        <YAxis type="number" dataKey="engagement" name="Credibility" unit="%" fontSize={12} stroke="#888" />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: '#111', border: '1px solid #333' }} />
                        <Scatter name="Reviews" data={correlationData} fill="hsl(var(--sentinel-positive))" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="platforms">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {platformPerformanceChart.map(p => (
                  <Card key={p.platform} className="glass-card border-border/50 p-4">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="font-semibold capitalize">{p.platform}</h3>
                      <span className="text-sm text-muted-foreground">{p.total} reviews</span>
                    </div>
                    <div className="h-4 w-full flex rounded-full overflow-hidden">
                      <div style={{ width: `${p.positive}%` }} className="bg-sentinel-positive h-full" title={`Positive: ${p.positive}%`} />
                      <div style={{ width: `${p.neutral}%` }} className="bg-muted-foreground/30 h-full" title={`Neutral: ${p.neutral}%`} />
                      <div style={{ width: `${p.negative}%` }} className="bg-sentinel-negative h-full" title={`Negative: ${p.negative}%`} />
                    </div>
                    <div className="flex justify-between text-xs mt-2 text-muted-foreground">
                      <span>Pos: {p.positive}%</span>
                      <span>Neg: {p.negative}%</span>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
};

export default Analytics;
