import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Sector } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Loader2, AlertCircle } from 'lucide-react';

interface EmotionData {
  name: string;
  value: number;
  color: string;
}

const defaultColors: Record<string, string> = {
  'Joy': '#22c55e',          // Vibrant Green
  'Trust': '#3b82f6',        // Bright Blue
  'Anticipation': '#f59e0b',  // Amber/Orange
  'Surprise': '#a855f7',     // Purple
  'Sadness': '#64748b',       // Blue Grey
  'Anger': '#ef4444',        // Red
  'Fear': '#1e293b',         // Dark Navy
  'Disgust': '#10b981',      // Emerald
};

interface EmotionWheelProps {
  isLoading?: boolean;
  data?: EmotionData[];
}

const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        className="drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]"
      />
    </g>
  );
};

export function EmotionWheel({ isLoading, data }: EmotionWheelProps) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-[350px] flex items-center justify-center animate-pulse">
        <Loader2 className="h-8 w-8 text-primary animate-spin opacity-50" />
      </div>
    );
  }

  // Use props data or show empty state
  const emotionData = data && data.length > 0
    ? data.map(d => ({
      ...d,
      color: d.color || defaultColors[d.name] || 'hsl(0, 0%, 50%)'
    }))
    : [];

  const isEmpty = emotionData.length === 0;

  // Placeholder data for beautiful empty state
  const placeholderData = [
    { name: 'Waiting', value: 100, color: 'rgba(255,255,255,0.03)' },
  ];

  return (
    <div className="glass-card p-6 h-[350px] flex flex-col relative overflow-hidden group">
      {/* Decorator background */}
      <div className="absolute top-0 right-0 p-24 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

      <div className="flex justify-between items-start mb-2 z-10">
        <div>
          <h3 className="text-lg font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
            Emotion DNA
          </h3>
          <p className="text-xs text-muted-foreground mt-1">Sentiment extraction engine</p>
        </div>
        {!isEmpty && (
          <div className="text-xs font-mono px-2 py-1 rounded bg-white/5 border border-white/10 text-muted-foreground">
            REAL-TIME
          </div>
        )}
      </div>

      <div className="flex-1 flex items-center justify-center relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <defs>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <Pie
              data={isEmpty ? placeholderData : emotionData}
              cx="50%"
              cy="50%"
              innerRadius={75}
              outerRadius={95}
              paddingAngle={isEmpty ? 0 : 4}
              dataKey="value"
              animationBegin={0}
              animationDuration={1500}
              stroke="none"
              cornerRadius={isEmpty ? 0 : 6}
              activeShape={isEmpty ? undefined : renderActiveShape}
            >
              {(isEmpty ? placeholderData : emotionData).map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  style={{ filter: !isEmpty ? 'url(#glow)' : undefined }}
                />
              ))}
            </Pie>
            {!isEmpty && <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload?.[0]?.payload;
                  if (!d) return null;
                  return (
                    <div className="glass-card px-3 py-2 border border-white/10 shadow-xl backdrop-blur-xl bg-black/80">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                        <span className="font-semibold text-sm">{d.name}</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 font-mono">
                        Impact: <span className="text-white font-bold">{d.value}%</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />}
          </PieChart>
        </ResponsiveContainer>

        {/* Center overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {isEmpty ? (
            <div className="text-center opacity-40 flex flex-col items-center">
              <div className="w-12 h-12 rounded-full border border-dashed border-white/20 flex items-center justify-center mb-2 animate-spin-slow">
                <AlertCircle className="w-5 h-5" />
              </div>
              <p className="text-xs font-medium">No Signal</p>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-3xl font-bold tracking-tighter text-white drop-shadow-lg">
                {emotionData[0]?.value}%
              </div>
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
                {emotionData[0]?.name}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modern Legend */}
      <AnimatePresence>
        {!isEmpty && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-4 gap-2 mt-4"
          >
            {emotionData.slice(0, 4).map((e) => (
              <div key={e.name} className="flex flex-col items-center justify-center p-2 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                <div className="w-1.5 h-1.5 rounded-full mb-1.5" style={{ background: e.color }} />
                <span className="text-[10px] text-muted-foreground font-medium truncate w-full text-center">{e.name}</span>
                <span className="text-xs font-bold text-white mt-0.5">{e.value}%</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
