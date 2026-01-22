
import { useQuery } from "@tanstack/react-query";

interface DashboardData {
  success: boolean;
  data: any; // Replace 'any' with specific type if available
}

const fetchDashboardData = async (): Promise<DashboardData> => {
  const response = await fetch("/api/dashboard");
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  return response.json();
};

export const useDashboardData = () => {
  const query = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboardData,
    refetchInterval: 3000, // 3 seconds heartbeat
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
  };
};
