import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';

export type DashboardStats = {
  totalReviews: number;
  sentimentScore: number;
  averageCredibility: number;
  platformBreakdown: Record<string, number>;
};

// Heartbeat hook: polls dashboard stats every 5 seconds
export function useRealtimeDashboard() {
  const {
    data,
    isLoading,
    refetch,
  } = useQuery<DashboardStats | null>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await getDashboardStats();
      // getDashboardStats is expected to return the payload directly
      return (res as DashboardStats) ?? null;
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
    staleTime: 0,
  });

  return { data, isLoading, refetch };
}

// Backwards-compatible export: some pages import `useDashboardData`
export function useDashboardData() {
  const { data, isLoading, refetch } = useRealtimeDashboard();

  // Normalize shape expected by older consumers: { metrics, loading, refetch }
  return { metrics: data, loading: isLoading, refetch };
}
