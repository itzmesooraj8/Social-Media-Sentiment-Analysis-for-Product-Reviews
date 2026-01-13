import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { cn } from '@/lib/utils';

interface EmotionData {
  name: string;
  value: number;
  color: string;
}

const emotionData: EmotionData[] = [
  { name: 'Joy', value: 35, color: 'hsl(142, 71%, 45%)' },
  { name: 'Trust', value: 25, color: 'hsl(199, 89%, 48%)' },
  { name: 'Anticipation', value: 15, color: 'hsl(38, 92%, 50%)' },
  { name: 'Surprise', value: 10, color: 'hsl(280, 70%, 50%)' },
  { name: 'Sadness', value: 8, color: 'hsl(220, 70%, 50%)' },
  { name: 'Anger', value: 4, color: 'hsl(0, 84%, 60%)' },
  { name: 'Fear', value: 2, color: 'hsl(260, 50%, 40%)' },
  { name: 'Disgust', value: 1, color: 'hsl(150, 30%, 40%)' },
];

interface EmotionWheelProps {
  isLoading?: boolean;
}

export function EmotionWheel({ isLoading }: EmotionWheelProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="h-[280px] flex items-center justify-center">
          <div className="w-48 h-48 rounded-full bg-muted/50" />
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass-card p-3 border border-border/50">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm text-muted-foreground">{data.value}% of reviews</p>
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="glass-card p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Emotion Detection</h3>
      <p className="text-sm text-muted-foreground mb-4">Distribution of emotions across all reviews</p>

      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={emotionData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              animationBegin={0}
              animationDuration={1000}
            >
              {emotionData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color}
                  stroke="hsl(0 0% 10%)"
                  strokeWidth={1}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="grid grid-cols-4 gap-2 mt-4">
        {emotionData.map((emotion) => (
          <div key={emotion.name} className="flex items-center gap-1.5">
            <div 
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: emotion.color }}
            />
            <span className="text-xs text-muted-foreground truncate">{emotion.name}</span>
          </div>
        ))}
      </div>

      {/* Top Emotions Summary */}
      <div className="mt-4 pt-4 border-t border-border/50">
        <h4 className="text-sm font-medium mb-3">Top Emotions</h4>
        <div className="space-y-2">
          {emotionData.slice(0, 3).map((emotion, index) => (
            <div key={emotion.name} className="flex items-center gap-3">
              <span className="text-xs font-medium text-muted-foreground w-4">{index + 1}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">{emotion.name}</span>
                  <span className="text-sm font-medium">{emotion.value}%</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${emotion.value}%` }}
                    transition={{ duration: 0.8, delay: 0.2 + index * 0.1 }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: emotion.color }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
