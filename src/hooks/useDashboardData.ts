import { useQuery } from '@tanstack/react-query';
import { sentinelApi } from '../lib/api';

export const useDashboardData = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      // Call the API method
      const stats = await sentinelApi.getDashboardStats();
      return stats;
    },
    // PDF Requirement: Real-Time Analysis with 3s polling
    refetchInterval: 3000,
    retry: 2
  });

  return { data, isLoading, refetch };
};