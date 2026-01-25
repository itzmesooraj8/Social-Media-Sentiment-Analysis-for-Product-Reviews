import { useQuery } from "@tanstack/react-query";
import api from "../lib/api";

export const useDashboardData = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
        const response = await api.getDashboardStats();
        return response; 
    },
    refetchInterval: 3000, // 3 Seconds (PDF Requirement: Real-Time Analysis)
  });

  return { data, isLoading, refetch };
};