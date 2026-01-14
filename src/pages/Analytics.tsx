// ... top of file ...
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
// ...
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
  const { data: dashboardData, isLoading: isDashboardLoading } = useDashboardData();
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch detailed analytics
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/analytics');
        const data = await response.json();
        if (data.success) {
          setAnalyticsData(data.data);
        }
      } catch (error) {
        console.error("Failed to fetch analytics", error);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  // Use real data from backend, defaulting to empty arrays if missing to avoid crashes
  const platformBreakdown = analyticsData?.platformBreakdown || {};
  const totalReviews = analyticsData?.totalAnalyzed || 0;

  // Transform platform data for charts (Real)
  const platformPerformanceChart = Object.entries(platformBreakdown).map(([platform, count]: [string, any]) => ({
    platform,
    total: count,
    // Since our simple backend metrics don't break down sentiment per platform yet, 
    // we calculate global ratios or default to 0. 
    // Ideally the backend /api/analytics should provide platform-specific sentiment counts.
    // For now, we will just show the volume.
    positive: 0,
    neutral: 0,
    negative: 0
  }));

  const sentimentTrends = dashboardData?.sentimentTrends || [];

  // No fake data. If endpoints don't provide these yet, show empty/loading state.
  const comparisonData: any[] = [];
  const engagementData: any[] = [];
  const correlationData: any[] = [];

  const stats = [
    {
      label: 'Avg Response Time',
      value: '2.4h',
      change: -15,
      icon: Zap,
      color: 'text-sentinel-positive'
    },
    {
      label: 'Engagement Rate',
      value: '4.8%',
      change: 8,
      icon: Target,
      color: 'text-sentinel-credibility'
    },
    {
      label: 'Sentiment Accuracy',
      value: '94.2%',
      change: 2.5,
      icon: Activity,
      color: 'text-sentinel-positive'
    },
    {
      label: 'Global Reach',
      value: '42 Countries',
      change: 5,
      icon: Globe,
      color: 'text-sentinel-credibility'
    },
  ];

  if (loading || isDashboardLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-muted-foreground">Loading Analytics...</div>
        </div>
      </DashboardLayout>
    );
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

        {/* Quick Stats */}
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
              <TabsTrigger value="comparison">Comparison</TabsTrigger>
              <TabsTrigger value="correlation">Correlation</TabsTrigger>
              <TabsTrigger value="platforms">Platforms</TabsTrigger>
            </TabsList>

            <TabsContent value="trends">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sentiment Area Chart */}
                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-sentinel-credibility" />
                      Sentiment Volume Over Time
                    </CardTitle>
                  </CardHeader>
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
                          <Area
                            type="monotone"
                            dataKey="positive"
                            stroke="hsl(var(--sentinel-positive))"
                            fill="url(#positiveGradient)"
                            strokeWidth={2}
                          />
                          <Area
                            type="monotone"
                            dataKey="negative"
                            stroke="hsl(var(--sentinel-negative))"
                            fill="url(#negativeGradient)"
                            strokeWidth={2}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Engagement Heatmap */}
                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-sentinel-positive" />
                      Hourly Engagement Pattern
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={engagementData}>
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
                          <Bar dataKey="engagement" radius={[4, 4, 0, 0]}>
                            {engagementData.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={entry.engagement > 500
                                  ? 'hsl(var(--sentinel-positive))'
                                  : entry.engagement > 300
                                    ? 'hsl(var(--sentinel-credibility))'
                                    : 'hsl(var(--muted-foreground))'
                                }
                              />
                            ))}
                          </Bar>
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
                    Year-over-Year Comparison
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={comparisonData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                        <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px'
                          }}
                        />
                        <Legend />
                        <Bar yAxisId="left" dataKey="thisYear" name="This Year" fill="hsl(var(--sentinel-positive))" radius={[4, 4, 0, 0]} />
                        <Bar yAxisId="left" dataKey="lastYear" name="Last Year" fill="hsl(var(--muted-foreground))" radius={[4, 4, 0, 0]} opacity={0.5} />
                        <Line yAxisId="right" type="monotone" dataKey="growth" name="Growth %" stroke="hsl(var(--sentinel-credibility))" strokeWidth={2} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="correlation">
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-sentinel-positive" />
                    Sentiment vs Engagement Correlation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                        <XAxis
                          type="number"
                          dataKey="sentiment"
                          name="Sentiment Score"
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                          label={{ value: 'Sentiment Score', position: 'bottom', fill: 'hsl(var(--muted-foreground))' }}
                        />
                        <YAxis
                          type="number"
                          dataKey="engagement"
                          name="Engagement"
                          stroke="hsl(var(--muted-foreground))"
                          fontSize={12}
                          label={{ value: 'Engagement', angle: -90, position: 'left', fill: 'hsl(var(--muted-foreground))' }}
                        />
                        <ZAxis type="number" dataKey="volume" range={[50, 400]} />
                        <Tooltip
                          cursor={{ strokeDasharray: '3 3' }}
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px'
                          }}
                        />
                        <Scatter
                          name="Reviews"
                          data={correlationData}
                          fill="hsl(var(--sentinel-credibility))"
                          opacity={0.7}
                        />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="platforms">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {platformPerformanceChart.map((platform) => (
                  <Card key={platform.platform} className="glass-card border-border/50">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>{platform.platform}</span>
                        <span className="text-sm font-normal text-muted-foreground">
                          {platform.total.toLocaleString()} reviews
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Positive</span>
                            <span className="text-sentinel-positive">{platform.positive}%</span>
                          </div>
                          <div className="h-2 rounded-full bg-muted overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${platform.positive}%` }}
                              transition={{ duration: 1, ease: 'easeOut' }}
                              className="h-full bg-sentinel-positive rounded-full"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Neutral</span>
                            <span className="text-muted-foreground">{platform.neutral}%</span>
                          </div>
                          <div className="h-2 rounded-full bg-muted overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${platform.neutral}%` }}
                              transition={{ duration: 1, ease: 'easeOut', delay: 0.1 }}
                              className="h-full bg-muted-foreground rounded-full"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Negative</span>
                            <span className="text-sentinel-negative">{platform.negative}%</span>
                          </div>
                          <div className="h-2 rounded-full bg-muted overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${platform.negative}%` }}
                              transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
                              className="h-full bg-sentinel-negative rounded-full"
                            />
                          </div>
                        </div>
                      </div>
                    </CardContent>
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
