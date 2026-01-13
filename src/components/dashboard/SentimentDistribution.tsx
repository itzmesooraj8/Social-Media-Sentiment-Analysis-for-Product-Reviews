import { motion } from 'framer-motion';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { SentimentDataPoint } from '@/types/sentinel';

interface SentimentDistributionProps {
  data: SentimentDataPoint[];
  isLoading?: boolean;
}

const COLORS = {
  positive: 'hsl(157, 100%, 50%)',
  neutral: 'hsl(220, 9%, 46%)',
  negative: 'hsl(0, 100%, 58%)',
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 rounded-xl shadow-lg border border-border/50">
        <p className="font-semibold text-foreground capitalize">{payload[0].name}</p>
        <p className="text-sm text-muted-foreground">
          <span className="font-medium">{payload[0].value}%</span> of reviews
        </p>
      </div>
    );
  }
  return null;
};

const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (percent < 0.05) return null;

  return (
    <text 
      x={x} 
      y={y} 
      fill="white" 
      textAnchor="middle" 
      dominantBaseline="central"
      className="text-xs font-semibold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function SentimentDistribution({ data, isLoading }: SentimentDistributionProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-[300px] animate-pulse">
        <div className="h-6 w-44 bg-muted rounded mb-4" />
        <div className="h-full w-full bg-muted/50 rounded-xl" />
      </div>
    );
  }

  // Calculate average sentiment distribution
  const avgPositive = data.reduce((sum, d) => sum + d.positive, 0) / data.length;
  const avgNeutral = data.reduce((sum, d) => sum + d.neutral, 0) / data.length;
  const avgNegative = data.reduce((sum, d) => sum + d.negative, 0) / data.length;

  const chartData = [
    { name: 'Positive', value: Math.round(avgPositive), color: COLORS.positive },
    { name: 'Neutral', value: Math.round(avgNeutral), color: COLORS.neutral },
    { name: 'Negative', value: Math.round(avgNegative), color: COLORS.negative },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
      className="glass-card p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
      
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={80}
              innerRadius={40}
              dataKey="value"
              strokeWidth={2}
              stroke="hsl(var(--background))"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              formatter={(value) => (
                <span className="text-sm text-muted-foreground">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
