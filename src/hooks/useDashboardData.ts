import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getDashboardData } from '@/lib/api';
import { subscribeToTable } from '@/lib/supabase';
import { DashboardData, DashboardFilters } from '@/types/sentinel';

// Hook for fetching REAL dashboard data - NO MOCK DATA
// Now enhanced with Supabase Realtime subscriptions!
export const useDashboardData = (filters?: Partial<DashboardFilters>) => {
  const queryClient = useQueryClient();

  // Setup Real-time subscriptions
  useEffect(() => {
    console.log('🔌 Connecting to Supabase Realtime...');

    // Subscribe to reviews
    const reviewsChannel = subscribeToTable('reviews', (payload) => {
      console.log('⚡ Realtime Update (Reviews):', payload);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['realtime-metrics'] });
    });

    // Subscribe to sentiment_analysis
    const sentimentChannel = subscribeToTable('sentiment_analysis', (payload) => {
      console.log('⚡ Realtime Update (Analysis):', payload);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    });

    return () => {
      console.log('🔌 Disconnecting Realtime...');
      reviewsChannel.unsubscribe();
      sentimentChannel.unsubscribe();
    };
  }, [queryClient]);

  return useQuery<DashboardData | null>({
    queryKey: ['dashboard', filters],
    queryFn: async () => {
      try {
        const response = await getDashboardData();
        if (response.success && response.data) {
          return response.data;
        }
        // Return null if no data - will show empty state
        return null;
      } catch (error) {
        // Return null on error - will show empty state
        return null;
      }
    },
    // No polling needed with Realtime!
    refetchInterval: false,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    retry: false,
  });
};

// Hook for real-time metrics
export const useRealTimeMetrics = () => {
  return useQuery({
    queryKey: ['realtime-metrics'],
    queryFn: async () => {
      const response = await getDashboardData();
      return response.success && response.data ? response.data.metrics : null;
    },
    refetchInterval: false,
    refetchOnWindowFocus: false,
    retry: false,
  });
};

// Hook for alerts
export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const response = await getDashboardData();
      return response.success && response.data ? response.data.alerts : [];
    },
    refetchInterval: false,
    refetchOnWindowFocus: false,
    retry: false,
  });
};
