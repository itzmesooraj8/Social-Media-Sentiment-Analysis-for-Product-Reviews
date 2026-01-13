import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Twitter, MessageSquare, Youtube, Users } from 'lucide-react';
import { PlatformBreakdown } from '@/types/sentinel';

interface PlatformChartProps {
  data: PlatformBreakdown[];
  isLoading?: boolean;
}

const platformLabels: Record<string, string> = {
  twitter: 'Twitter/X',
  reddit: 'Reddit',
  youtube: 'YouTube',
  forums: 'Forums',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-4 rounded-xl shadow-lg border border-border/50">
        <p className="font-semibold text-foreground mb-2">
          {platformLabels[label] || label}
        </p>
        <div className="space-y-1">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.fill }}
              />
              <span className="text-muted-foreground capitalize">{entry.dataKey}:</span>
              <span className="font-medium">{entry.value}%</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-2 pt-2 border-t border-border/50">
          Total: {payload[0]?.payload?.total?.toLocaleString()} reviews
        </p>
      </div>
    );
  }
  return null;
};

export function PlatformChart({ data, isLoading }: PlatformChartProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-[300px] animate-pulse">
        <div className="h-6 w-44 bg-muted rounded mb-4" />
        <div className="h-full w-full bg-muted/50 rounded-xl" />
      </div>
    );
  }

  const chartData = data.map(item => ({
    ...item,
    name: platformLabels[item.platform],
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.7 }}
      className="glass-card p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Platform Breakdown</h3>
      
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
          >
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="hsl(var(--border))" 
              opacity={0.3}
              horizontal={true}
              vertical={false}
            />
            <XAxis 
              type="number" 
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              type="category" 
              dataKey="name"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              width={70}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--accent) / 0.3)' }} />
            <Legend 
              verticalAlign="top"
              height={36}
              iconType="circle"
            />
            <Bar 
              dataKey="positive" 
              name="Positive"
              stackId="sentiment"
              fill="hsl(157, 100%, 50%)"
              radius={[0, 0, 0, 0]}
            />
            <Bar 
              dataKey="neutral" 
              name="Neutral"
              stackId="sentiment"
              fill="hsl(220, 9%, 46%)"
            />
            <Bar 
              dataKey="negative" 
              name="Negative"
              stackId="sentiment"
              fill="hsl(0, 100%, 58%)"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
