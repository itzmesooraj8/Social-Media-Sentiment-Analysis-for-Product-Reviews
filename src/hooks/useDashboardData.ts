import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';

export const useRealtimeDashboard = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 3000, // The Heartbeat
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
};

export const useDashboardData = useRealtimeDashboard;