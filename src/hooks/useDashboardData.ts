import { useState, useEffect, useCallback } from 'react';

export type DashboardStats = {
  totalReviews: number;
  sentimentScore: number;
  averageCredibility: number;
  platformBreakdown: Record<string, number>;
};

export function useRealtimeDashboard(pollInterval = 30000) {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${import.meta.env.VITE_API_URL}/api/dashboard`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const payload = json.data || json;
      setData({
        totalReviews: payload.totalReviews ?? payload.metrics?.totalReviews ?? 0,
        sentimentScore: payload.sentimentScore ?? payload.metrics?.sentimentDelta ?? 0,
        averageCredibility: payload.averageCredibility ?? payload.metrics?.averageCredibility ?? 0,
        platformBreakdown: payload.platformBreakdown ?? payload.platformBreakdown ?? {},
      });
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, pollInterval);
    return () => clearInterval(id);
  }, [fetchData, pollInterval]);

  return { data, loading, error, refresh: fetchData };
}
import { useState, useEffect } from 'react';
import { getDashboardStats, getAnalytics, getAlerts } from '@/lib/api';
import { useToast } from './use-toast';
import { useQuery } from '@tanstack/react-query';

export function useDashboardData() {
  const { toast } = useToast();

  // 1. Fetch Dashboard Metrics - Optimized for performance
  const {
    data: metrics,
    isLoading: isLoadingMetrics,
    refetch: refetchMetrics
  } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const res = await getDashboardStats();
      return res;
    },
    refetchInterval: 60000, // Refresh every 60 seconds (not 5)
    staleTime: 30000, // Consider data fresh for 30 seconds
  });

  // 2. Fetch Analytics Data - Less frequent updates
  const {
    data: analytics,
    isLoading: isLoadingAnalytics
  } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => getAnalytics('7d'),
    refetchInterval: 120000, // Update every 2 minutes
    staleTime: 60000, // Fresh for 1 minute
  });

  // 3. Fetch Alerts - Less frequent
  const {
    data: alertsData,
    isLoading: isLoadingAlerts
  } = useQuery({
    queryKey: ['dashboard-alerts'],
    queryFn: getAlerts,
    refetchInterval: 60000, // Every 60 seconds
    staleTime: 30000,
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
