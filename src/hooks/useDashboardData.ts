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