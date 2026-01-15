import { motion } from 'framer-motion';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/lib/utils';


const sentimentColors = {
  positive: 'hsl(142, 71%, 45%)',
  neutral: 'hsl(0, 0%, 50%)',
  negative: 'hsl(0, 84%, 60%)',
};

interface TopicData {
  name: string;
  size: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  keywords: string[];
}

interface TopicClustersProps {
  isLoading?: boolean;
  data?: TopicData[];
}

const CustomContent = (props: any) => {
  const { x, y, width, height, name, sentiment } = props;

  // Safety checks
  if (!name || width < 40 || height < 30) return null;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={sentimentColors[sentiment as keyof typeof sentimentColors] || sentimentColors.neutral}
        stroke="hsl(0, 0%, 10%)"
        strokeWidth={2}
        rx={4}
        style={{ transition: 'all 0.3s ease' }}
      />
      {width > 60 && height > 40 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="white"
          fontSize={Math.min(12, width / 8)}
          fontWeight={500}
          style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
        >
          {name && name.length > 15 ? name.substring(0, 15) + '...' : name}
        </text>
      )}
    </g>
  );
};

export function TopicClusters(props: TopicClustersProps) {
  if (props.isLoading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 w-40 bg-muted rounded mb-4" />
        <div className="h-[300px] bg-muted/50 rounded-lg" />
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length && payload[0]?.payload) {
      const data = payload[0].payload;
      return (
        <div className="glass-card p-3 border border-border/50 max-w-xs">
          <p className="font-medium mb-1">{data.name || 'Unknown'}</p>
          <p className="text-sm text-muted-foreground mb-2">{data.size || 0} mentions</p>
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: sentimentColors[data.sentiment as keyof typeof sentimentColors] || sentimentColors.neutral }}
            />
            <span className="text-sm capitalize">{data.sentiment || 'neutral'} sentiment</span>
          </div>
          {data.keywords && data.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {data.keywords.map((keyword: string, idx: number) => (
                <span key={`${keyword}-${idx}`} className="text-xs bg-muted px-1.5 py-0.5 rounded">
                  {keyword}
                </span>
              ))}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Support prop-driven data or fetch from API
  const { data: topicsFromApi } = useQuery({
    queryKey: ['topics'],
    queryFn: async () => {
      const res = await fetch('/api/analytics/topics');
      const json = await res.json();
      return json.data || [];
    },
    enabled: !props.data
  });

  const activeData: TopicData[] = (props as TopicClustersProps).data || topicsFromApi || [];

  const treemapData = activeData.map(topic => ({
    ...topic,
    children: [{ name: topic.name, size: topic.size, sentiment: topic.sentiment, keywords: topic.keywords }],
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
      className="glass-card p-6"
    >
      <h3 className="text-lg font-semibold mb-2">Topic Clusters</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Key discussion topics sized by mention volume
      </p>

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <Treemap
            data={treemapData}
            dataKey="size"
            aspectRatio={4 / 3}
            stroke="hsl(0, 0%, 10%)"
            content={<CustomContent />}
          >
            <Tooltip content={<CustomTooltip />} />
          </Treemap>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-border/50">
        {Object.entries(sentimentColors).map(([sentiment, color]) => (
          <div key={sentiment} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-sm text-muted-foreground capitalize">{sentiment}</span>
          </div>
        ))}
      </div>

      {/* Top Topics List */}
      <div className="mt-4 pt-4 border-t border-border/50">
        <h4 className="text-sm font-medium mb-3">Top Discussion Topics</h4>
        <div className="grid grid-cols-2 gap-2">
          {(activeData || []).slice(0, 4).map((topic, index) => (
            <div
              key={topic.name}
              className="flex items-center gap-2 p-2 rounded-lg bg-background/50"
            >
              <span className="text-xs font-medium text-muted-foreground w-4">
                {index + 1}
              </span>
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: sentimentColors[topic.sentiment] }}
              />
              <span className="text-sm truncate">{topic.name}</span>
              <span className="text-xs text-muted-foreground ml-auto">{topic.size}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
