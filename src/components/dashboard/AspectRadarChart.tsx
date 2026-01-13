import { motion } from 'framer-motion';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { AspectScore } from '@/types/sentinel';

interface AspectRadarChartProps {
  data: AspectScore[];
  isLoading?: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="glass-card p-3 rounded-xl shadow-lg border border-border/50">
        <p className="font-semibold text-foreground">{data.aspect}</p>
        <p className="text-sm text-muted-foreground">
          Score: <span className="font-medium text-sentinel-positive">{data.score.toFixed(1)}</span>
        </p>
        <p className="text-xs text-muted-foreground">
          {data.reviewCount.toLocaleString()} reviews
        </p>
      </div>
    );
  }
  return null;
};

export function AspectRadarChart({ data, isLoading }: AspectRadarChartProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-[350px] animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="h-full w-full bg-muted/50 rounded-xl" />
      </div>
    );
  }

  // Transform data for radar chart (scale 0-5 to 0-100 for better visualization)
  const chartData = data.map(item => ({
    ...item,
    value: (item.score / 5) * 100,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="glass-card p-6 h-[350px]"
    >
      <h3 className="text-lg font-semibold mb-4">Aspect Analysis</h3>
      
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
            <PolarGrid 
              stroke="hsl(var(--border))" 
              opacity={0.5}
            />
            <PolarAngleAxis
              dataKey="aspect"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              tickFormatter={(value) => `${(value / 20).toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Radar
              name="Score"
              dataKey="value"
              stroke="hsl(157, 100%, 50%)"
              fill="hsl(157, 100%, 50%)"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
