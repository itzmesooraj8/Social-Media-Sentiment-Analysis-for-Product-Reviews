import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';

export type DashboardStats = {
  metrics?: {
    totalReviews?: number;
    sentimentDelta?: number;
    averageCredibility?: number | null;
    botsDetected?: number;
  };
  recentReviews?: any[];
  platformBreakdown?: Record<string, any> | any[];
  alerts?: any[];
  aiSummary?: string | null;
};

// Heartbeat hook: polls dashboard stats every 3 seconds to provide a "real-time" feel
export function useRealtimeDashboard() {
  const query = useQuery<DashboardStats | null>(
    ['dashboard-stats'],
    async () => {
      try {
        const res = await getDashboardStats();
        return (res as any)?.data ?? (res as any) ?? null;
      } catch (e) {
        return null;
      }
    },
    {
      refetchInterval: 3000, // CRITICAL: 3 seconds heartbeat
      refetchIntervalInBackground: true,
      staleTime: 0,
      retry: false,
    }
  );

  return { data: query.data, isLoading: query.isLoading, refetch: query.refetch };
}

// Backwards-compatible alias
export function useDashboardData() {
  const { data, isLoading, refetch } = useRealtimeDashboard();
  return { metrics: data, loading: isLoading, refetch };
}
