import { useQuery } from '@tanstack/react-query';
import { getDashboardStats, getTopics, getAnalytics } from '@/lib/api';

export const useRealtimeDashboard = () => {
  return useQuery({
    queryKey: ['dashboard-aggregated'],
    queryFn: async () => {
      const [stats, topics, analytics] = await Promise.all([
        getDashboardStats(),
        getTopics(15),
        getAnalytics('7d')
      ]);

      // Merge data
      return {
        ...stats,
        data: {
          ...(stats?.data || {}),
          recentReviews: (stats?.data?.recentReviews || []).map((r: any) => {
            const sa = Array.isArray(r.sentiment_analysis) ? r.sentiment_analysis[0] : r.sentiment_analysis;
            return {
              id: r.id,
              text: r.content || "",
              platform: r.platform || "unknown",
              username: r.username || r.author || "Anonymous",
              timestamp: r.created_at,
              sentiment: (sa?.label || 'neutral').toLowerCase(),
              sentiment_label: sa?.label || 'NEUTRAL',
              sourceUrl: r.url || "",
              credibility: sa?.credibility,
              like_count: r.likes || r.like_count || 0
            };
          }),
          topKeywords: topics || [], // Map topics to keywords
          sentimentTrends: analytics?.data?.sentimentTrends || []
        }
      };
    },
    refetchInterval: 5000,
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
};

export const useDashboardData = useRealtimeDashboard;