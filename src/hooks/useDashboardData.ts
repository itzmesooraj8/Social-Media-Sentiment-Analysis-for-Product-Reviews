import { useState, useEffect } from 'react';
import { getDashboardStats, getAnalytics, getAlerts } from '@/lib/api';
import { useToast } from './use-toast';
import { useQuery } from '@tanstack/react-query';

export function useDashboardData() {
  const { toast } = useToast();

  // 1. Fetch Dashboard Metrics with Auto-Refresh
  const {
    data: metrics,
    isLoading: isLoadingMetrics,
    refetch: refetchMetrics
  } = useQuery({
    queryKey: ['dashboard-metrics'],
    // Using getDashboardData as it returns the comprehensive metrics structure expected by the dashboard
    queryFn: async () => {
      const res = await getDashboardStats();
      return res;
    },
    refetchInterval: 5000, // ⚡ AUTO-REFRESH every 5 seconds
  });

  // 2. Fetch Analytics Data
  const {
    data: analytics,
    isLoading: isLoadingAnalytics
  } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => getAnalytics('7d'),
    refetchInterval: 10000, // Update charts every 10s
  });

  // 3. Fetch Alerts
  // Assuming getAlerts returns { success: true, data: [...] }
  const {
    data: alertsData,
    isLoading: isLoadingAlerts
  } = useQuery({
    queryKey: ['dashboard-alerts'],
    queryFn: getAlerts,
    refetchInterval: 5000,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoadingMetrics && !isLoadingAnalytics && !isLoadingAlerts) {
      setLoading(false);
    }
  }, [isLoadingMetrics, isLoadingAnalytics, isLoadingAlerts]);

  return {
    metrics,
    analytics,
    alerts: alertsData || [],
    loading,
    refresh: () => {
      refetchMetrics();
      toast({ title: "Refreshing data..." });
    }
  };
}
