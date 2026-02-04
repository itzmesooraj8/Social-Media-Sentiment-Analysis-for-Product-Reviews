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
    const data = payload?.[0]?.payload;
    if (!data) return null;
    return (
      <div className="glass-card p-3 rounded-xl shadow-lg border border-border/50">
        <p className="font-semibold text-foreground">{data?.aspect || 'Unknown'}</p>
        <p className="text-sm text-muted-foreground">
          Score: <span className="font-medium text-sentinel-positive">{(data?.score || 0).toFixed(1)}</span>
        </p>
        <p className="text-xs text-muted-foreground">
          {(data?.reviewCount || 0).toLocaleString()} reviews
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

  const isEmpty = !data || data.length === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="glass-card p-6 h-[350px]"
    >
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        Aspect Analysis
        {isEmpty && <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-white/5 text-muted-foreground animate-pulse">STANDBY</span>}
      </h3>

      <div className="h-[280px] w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart
            data={isEmpty ? [
              { aspect: 'Price', value: 100 },
              { aspect: 'Quality', value: 100 },
              { aspect: 'Service', value: 100 },
              { aspect: 'Usability', value: 100 },
              { aspect: 'Features', value: 100 },
            ] : chartData}
            margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
          >
            <PolarGrid
              stroke={isEmpty ? "rgba(255,255,255,0.05)" : "hsl(var(--border))"}
              strokeDasharray={isEmpty ? "4 4" : undefined}
              opacity={isEmpty ? 0.3 : 0.5}
            />
            <PolarAngleAxis
              dataKey="aspect"
              tick={{ fill: isEmpty ? 'rgba(255,255,255,0.1)' : 'hsl(var(--muted-foreground))', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={isEmpty ? false : { fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              axisLine={!isEmpty}
              tickFormatter={(value) => `${(value / 20).toFixed(0)}`}
            />
            {!isEmpty && <Tooltip content={<CustomTooltip />} />}

            {!isEmpty ? (
              <Radar
                name="Score"
                dataKey="value"
                stroke="hsl(157, 100%, 50%)"
                fill="hsl(157, 100%, 50%)"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            ) : (
              // Empty state "Ghost" radar
              <Radar
                name="Scanning"
                dataKey="value"
                stroke="transparent"
                fill="transparent"
              />
            )}
          </RadarChart>
        </ResponsiveContainer>

        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            {/* Radar Scanner Animation */}
            <div className="w-48 h-48 rounded-full border border-white/5 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-spin-slow w-full h-full origin-bottom-right opacity-30"
                style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 0)' }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-xs text-muted-foreground/50 tracking-widest uppercase">Initializing</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
