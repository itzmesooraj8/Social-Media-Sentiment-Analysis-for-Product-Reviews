
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { ExportButton } from '@/components/ExportButton';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { FileText, BarChart3, Shield } from 'lucide-react';
import { ReviewFeed } from '@/components/dashboard/ReviewFeed';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { getProductStats, triggerScrape, getReviews } from '@/lib/api';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useToast } from '@/hooks/use-toast';

export default function ProductDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);

  // Aggressive Polling Mode: 1s interval when analyzing, 15s otherwise
  const pollInterval = isAnalyzing ? 1000 : 15000;

  // Fetch product specific reviews/stats
  const { data: reviewsData } = useQuery({
    queryKey: ['reviews', id],
    queryFn: async () => {
      const data = await getReviews(id!, 50);
      return { data };
    },
    refetchInterval: pollInterval
  });

  const { data: statsData } = useQuery({
    queryKey: ['productStats', id],
    queryFn: () => getProductStats(id!),
    enabled: !!id,
    refetchInterval: pollInterval
  });

  const reviews = reviewsData?.data || [];

  // Use real aggregated stats from backend
  const backendCount = statsData?.totalReviews ?? statsData?.total_reviews ?? 0;
  const listCount = reviews.length;
  // Fallback to list count if backend count is missing or suspiciously zero while list has items
  const totalReviews = backendCount > 0 ? backendCount : listCount;

  const avgSentiment = statsData?.avgSentiment ?? statsData?.average_sentiment ?? 0; // 0-100 scale from backend
  const displayScore = (avgSentiment / 100).toFixed(2);

  // Analyze emotions from the new model (Most recent review)
  // Emotion Data for Chart
  const emotionData = statsData?.emotions || [];

  // Aspect Data for Chart
  const aspectData = statsData?.aspects || [];

  // Keywords
  const keywords = statsData?.keywords || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/products')}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Back
            </Button>
            <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              Product Analysis
              {isAnalyzing && (
                <span className="text-xs bg-yellow-500/10 text-yellow-500 px-2 py-0.5 rounded animate-pulse border border-yellow-500/20">
                  ⚡ Live Syncing...
                </span>
              )}
            </h2>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={isAnalyzing}
              onClick={async () => {
                if (!id) return;
                setIsAnalyzing(true);
                toast({ title: "Initializing Live Scrapers", description: "Spinning up AI agents to find real-time data..." })
                try {
                  await triggerScrape(id);
                  // Force aggressive polling for 30 seconds
                  setTimeout(() => {
                    setIsAnalyzing(false);
                    toast({ title: "Sync Complete", description: "Live analysis finished." });
                  }, 30000);

                  toast({ title: "Scrape Job Started", description: "Agents are hunting for reviews. Charts will update automatically." });
                } catch (e) {
                  setIsAnalyzing(false);
                  toast({ title: "Scrape Error", description: "Could not start agents.", variant: "destructive" });
                }
              }}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
              {isAnalyzing ? 'Analyzing...' : 'Live Analysis'}
            </Button>
            {id && <ExportButton productId={id} />}
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            title="Total Reviews"
            value={totalReviews}
            icon={FileText}
            accentColor="neutral"
            subtitle="Analyzed"
          />
          <MetricCard
            title="Avg Sentiment"
            value={displayScore}
            icon={BarChart3}
            accentColor={parseFloat(displayScore) > 0.6 ? 'positive' : 'negative'}
            subtitle="Score (0-1)"
          />
          <MetricCard
            title="Credibility"
            value={statsData?.credibility_score ? `${statsData.credibility_score}%` : 'N/A'}
            icon={Shield}
            accentColor="credibility"
            subtitle="Trust Score"
          />
          <MetricCard
            title="Primary Emotion"
            value={emotionData?.[0]?.name || 'N/A'}
            icon={Shield}
            accentColor="credibility"
            subtitle="Dominant Feel"
          />
        </div>

        {/* GOD TIER SECTION: Aspects & Emotions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          {/* 1. Emotion Profile */}
          <div className={`p-6 border rounded-xl bg-card/50 backdrop-blur-sm shadow-sm border-white/5 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
            <h3 className="font-semibold mb-6 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-500" /> Emotional Profile
            </h3>
            <div className="h-[250px]">
              {emotionData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={emotionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {emotionData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={['#8b5cf6', '#ef4444', '#10b981', '#f59e0b', '#3b82f6'][index % 5]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151' }} itemStyle={{ color: '#f3f4f6' }} />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="h-6 w-6 animate-spin text-yellow-500" />
                      <span>Analyzing Emotions...</span>
                    </>
                  ) : "No emotion data available"}
                </div>
              )}
            </div>
          </div>

          {/* 2. Aspect Sentiment Radar */}
          <div className={`p-6 border rounded-xl bg-card/50 backdrop-blur-sm shadow-sm border-white/5 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
            <h3 className="font-semibold mb-6 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500" /> Aspect Analysis
            </h3>
            <div className="h-[250px]">
              {aspectData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={aspectData} layout="vertical" margin={{ left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} hide />
                    <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 12 }} interval={0} />
                    <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151' }} />
                    <Bar dataKey="score" name="Positive %" radius={[0, 4, 4, 0]}>
                      {aspectData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.score > 70 ? '#10b981' : entry.score < 40 ? '#ef4444' : '#f59e0b'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="h-6 w-6 animate-spin text-yellow-500" />
                      <span>Extracting Aspects...</span>
                    </>
                  ) : "No aspect data detected"}
                </div>
              )}
            </div>
          </div>

          {/* 3. Top Keywords */}
          <div className={`p-6 border rounded-xl bg-card/50 backdrop-blur-sm shadow-sm border-white/5 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
            <h3 className="font-semibold mb-6 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-pink-500" /> Trending Topics
            </h3>
            <div className="flex flex-wrap gap-2 content-start h-[250px] overflow-y-auto pr-2">
              {keywords.length > 0 ? (
                keywords.map((k: any, i: number) => (
                  <div key={i} className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs hover:bg-white/10 transition-colors flex items-center gap-2">
                    <span className="text-foreground/90">{k.text}</span>
                    <span className="text-[10px] text-muted-foreground bg-black/20 px-1.5 rounded">{k.value}</span>
                  </div>
                ))
              ) : (
                <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="h-6 w-6 animate-spin text-yellow-500" />
                      <span>Identifiying Topics...</span>
                    </>
                  ) : "No topics found"}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Charts area placeholder */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm">
            <h3 className="font-semibold mb-4 text-center">Recent Reviews (Live Feed)</h3>
            <ReviewFeed reviews={reviews} />
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
