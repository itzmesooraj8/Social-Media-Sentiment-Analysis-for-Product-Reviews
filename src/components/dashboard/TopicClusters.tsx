
import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Hash, TrendingUp } from 'lucide-react';
import { useDashboardData } from '@/hooks/useDashboardData';

interface Topic {
  text: string;
  value: number;
}

interface TopicClustersProps {
  isLoading?: boolean;
}

export const TopicClusters = ({ isLoading }: TopicClustersProps) => {
  const { data } = useDashboardData();
  const keywords = data?.topKeywords || [];

  // Determine size classes based on value (frequency)
  const getSizeClass = (value: number, max: number) => {
    const ratio = value / (max || 1);
    if (ratio > 0.8) return 'text-xl px-4 py-2';
    if (ratio > 0.5) return 'text-lg px-3 py-1.5';
    return 'text-sm px-2 py-1';
  };

  const maxVal = Math.max(...keywords.map((k: any) => k.value), 1);

  return (
    <Card className="glass-card border-border/50 h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Hash className="h-5 w-5 text-sentinel-highlight" />
            Emerging Topics (AI)
          </CardTitle>
          <Badge variant="outline" className="text-xs font-mono">
            Live Analysis
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex flex-wrap gap-2 animate-pulse">
             {[1,2,3,4,5].map(i => (
               <div key={i} className="h-8 w-24 bg-muted rounded-full" />
             ))}
          </div>
        ) : keywords.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
            <TrendingUp className="h-8 w-8 mb-2 opacity-50" />
            <p>No topics extracted yet.</p>
            <p className="text-xs">Analyze reviews to generate topics.</p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-3 items-center justify-center min-h-[200px] content-center">
            {keywords.map((topic: any, idx: number) => (
              <Badge
                key={idx}
                variant="secondary"
                className={`cursor-default transition-all hover:scale-110 hover:bg-sentinel-highlight hover:text-white ${getSizeClass(topic.value, maxVal)}`}
                title={`${topic.value} mentions`}
              >
                {topic.text}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
