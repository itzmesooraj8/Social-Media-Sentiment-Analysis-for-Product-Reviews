
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { ExportButton } from '@/components/ExportButton';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { FileText, BarChart3, Shield } from 'lucide-react';
import { ReviewFeed } from '@/components/dashboard/ReviewFeed';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { getProductStats } from '@/lib/api';

export default function ProductDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Fetch product specific reviews/stats
  const { data: reviewsData } = useQuery({
    queryKey: ['reviews', id],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/reviews?product_id=${id}&limit=100`);
      if (!res.ok) throw new Error('Failed to fetch reviews');
      return res.json();
    }
  });

  const { data: statsData } = useQuery({
    queryKey: ['productStats', id],
    queryFn: () => getProductStats(id!),
    enabled: !!id,
    refetchInterval: 5000 // Real-time poll
  });

  const reviews = reviewsData?.data || [];
  
  // Use real aggregated stats from backend
  const totalReviews = statsData?.total_reviews || 0;
  const avgSentiment = statsData?.average_sentiment || 0; // 0-100 scale from backend
  
  // Convert 0-100 back to 0-1 for display if needed, or keep as %
  // The backend now returns avg_sentiment (0-100) and positive_percent (0-100).
  // Let's assume user wants 0-1 scale for "Score" based on existing UI, or we can adapt.
  // The existing UI said "Score (0-1)". Let's map 0-100 -> 0-1.
  const displayScore = (avgSentiment / 100).toFixed(2);

  // Analyze emotions from the new model (Most recent review)
  // We look at the first sentiment analysis entry of the most recent review
  const latestEmotion = reviews[0]?.sentiment_analysis?.[0]?.emotions?.[0]?.name || 
                        reviews[0]?.sentiment_analysis?.[0]?.emotions?.[0] || 'neutral';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/products')}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Back
            </Button>
            <h2 className="text-2xl font-bold tracking-tight">Product Analysis</h2>
          </div>
          {/* HERE IS THE EXPORT BUTTON */}
          {id && <ExportButton productId={id} />}
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="Total Reviews"
            value={totalReviews}
            icon={FileText}
            accentColor="positive"
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
            title="Latest Emotion"
            value={latestEmotion}
            icon={Shield}
            accentColor="credibility"
            subtitle="Most recent"
          />
        </div>

        {/* Charts area placeholder */}
         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
           <div className="p-4 border rounded-lg bg-card text-card-foreground shadow-sm">
             <h3 className="font-semibold mb-4">Recent Reviews</h3>
             <ReviewFeed reviews={reviews} />
           </div>
         </div>

      </div>
    </DashboardLayout>
  );
}
