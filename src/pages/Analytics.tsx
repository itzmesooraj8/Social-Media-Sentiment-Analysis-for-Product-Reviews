import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Skeleton } from '@/components/ui/skeleton';
import {
  TrendingUp, TrendingDown, BarChart3, Zap, Globe, Target, Activity, LineChart as LineChartIcon
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useDashboardData } from '@/hooks/useDashboardData';
import { getAnalytics, getExecutiveSummary, getPredictiveAnalytics, getProducts } from '@/lib/api';
import { WordCloudPanel } from '@/components/dashboard/WordCloudPanel';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ComposedChart, Line, Legend, ScatterChart, Scatter,
  LineChart
} from 'recharts';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const Analytics = () => {
  const navigate = useNavigate();

  // 1. Fetch Core Data
  const { data: dashboardData, isLoading: isDashboardLoading } = useDashboardData();

  // 2. Fetch Products to drive Predictive AI
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: getProducts });
  const firstProductId = products?.[0]?.id;

  // 3. Predictive AI Query
  const { data: predictionRes, isLoading: isPredicting } = useQuery({
    queryKey: ['prediction', firstProductId],
    queryFn: () => getPredictiveAnalytics(firstProductId!, 7),
    enabled: !!firstProductId
  });

  const { data: analyticsRes, isLoading: isAnalyticsLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => getAnalytics('7d'),
    refetchInterval: 10000
  });

  const { data: summaryRes } = useQuery({
    queryKey: ['executiveSummary'],
    queryFn: getExecutiveSummary,
  });

  const loading = isDashboardLoading || isAnalyticsLoading;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-8 space-y-4">
          <Skeleton className="h-12 w-1/3" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
          <Skeleton className="h-[400px] w-full" />
        </div>
      </DashboardLayout>
    );
  }

  const analyticsData = analyticsRes?.success ? analyticsRes.data : null;
  const metrics = (dashboardData as any)?.data || {}; // API returns flat stats structure
  // Prioritize analytics endpoint for trends
  const sentimentTrends = analyticsData?.sentimentTrends || (dashboardData as any)?.data?.sentimentTrends || [];
  const forecastData = (predictionRes?.success && predictionRes.data?.forecast) ? predictionRes.data.forecast : [];
  const trendDirection = predictionRes?.success ? predictionRes.data?.trend : null;

  // Stats Array - NO HARDCODED FALLBACKS - show real data or "-"
  const stats = [
    { label: 'Total Reviews', value: metrics.totalReviews ?? '-', change: 0, icon: Zap, color: 'text-sentinel-positive' },
    { label: 'Sentiment Score', value: metrics.sentimentDelta ? `${metrics.sentimentDelta.toFixed(1)}%` : '-', change: 0, icon: Target, color: 'text-sentinel-credibility' },
    { label: 'Avg Credibility', value: metrics.averageCredibility ? `${metrics.averageCredibility.toFixed(1)}%` : '-', change: 0, icon: Activity, color: 'text-sentinel-positive' },
    { label: 'Future Sentiment', value: trendDirection ? trendDirection.toUpperCase() : '-', change: 0, icon: LineChartIcon, color: trendDirection === 'improving' ? 'text-green-500' : 'text-yellow-500' },
  ];

  return (
    <DashboardLayout>
      <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">

        {/* Header */}
        <div className="flex justify-between items-end">
          <motion.div variants={itemVariants}>
            <h1 className="text-2xl font-bold">Advanced Analytics</h1>
            <p className="text-muted-foreground">Real-time insights & AI forecasting</p>
          </motion.div>
          {summaryRes?.summary && (
            <div className="hidden md:block text-xs bg-muted/50 p-2 rounded max-w-md border border-sentinel-credibility/20">
              <span className="font-bold text-sentinel-credibility">AI Insight:</span> {summaryRes.summary.substring(0, 120)}...
            </div>
          )}
        </div>

        {/* KPI Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label} className="glass-card border-border/50">
              <CardContent className="pt-6">
                <div className="flex justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-2xl font-bold mt-1">{stat.value}</p>
                  </div>
                  <stat.icon className={`h-8 w-8 ${stat.color} opacity-80`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>

        {/* Main Charts Area */}
        <motion.div variants={itemVariants}>
          <Tabs defaultValue="forecast" className="space-y-4">
            <TabsList className="glass-card border-border/50 w-full justify-start">
              <TabsTrigger value="forecast" className="data-[state=active]:bg-sentinel-credibility data-[state=active]:text-white">
                🔮 AI Forecast (Next 7 Days)
              </TabsTrigger>
              <TabsTrigger value="trends">Historical Trends</TabsTrigger>
              <TabsTrigger value="platforms">Platform Split</TabsTrigger>

            </TabsList>

            {/* TAB: AI FORECAST */}
            <TabsContent value="forecast">
              <Card className="glass-card border-sentinel-credibility/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-400" />
                    Predictive Sentiment Modeling
                  </CardTitle>
                  <CardDescription>
                    Using Linear Regression to project customer satisfaction for the coming week.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    {forecastData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={forecastData}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                          <XAxis dataKey="date" stroke="#888" fontSize={12} tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, { weekday: 'short' })} />
                          <YAxis domain={[0, 1]} stroke="#888" fontSize={12} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1f1f1f', borderColor: '#333' }}
                            formatter={(val: number) => [`${(val * 100).toFixed(1)}%`, 'Projected Score']}
                          />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="sentiment"
                            name="AI Projection"
                            stroke="hsl(var(--sentinel-credibility))"
                            strokeWidth={3}
                            dot={{ r: 4, fill: 'hsl(var(--sentinel-credibility))' }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-full items-center justify-center text-muted-foreground">
                        No enough data points to generate forecast yet. Try scraping more tweets.
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: HISTORICAL */}
            <TabsContent value="trends">
              <Card className="glass-card border-border/50">
                <CardHeader><CardTitle>Historical Volume</CardTitle></CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={sentimentTrends}>
                        <defs>
                          <linearGradient id="positiveGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--sentinel-positive))" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="hsl(var(--sentinel-positive))" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                        <XAxis dataKey="date" stroke="#888" fontSize={12} />
                        <YAxis stroke="#888" fontSize={12} />
                        <Tooltip contentStyle={{ backgroundColor: '#1f1f1f', borderColor: '#333' }} />
                        <Area type="monotone" dataKey="positive" stroke="hsl(var(--sentinel-positive))" fill="url(#positiveGradient)" />
                        <Area type="monotone" dataKey="negative" stroke="hsl(var(--sentinel-negative))" fill="red" fillOpacity={0.1} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>



            {/* TAB: PLATFORMS */}
            <TabsContent value="platforms">
              <Card className="glass-card border-border/50">
                <CardContent className="pt-6">
                  <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                    Select a product to view platform specific breakdown.
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
};

export default Analytics;
