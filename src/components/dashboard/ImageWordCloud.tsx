import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Cloud, Loader2, AlertCircle } from 'lucide-react';
import { getWordCloud } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

interface ImageWordCloudProps {
  productId?: string;
}

export function ImageWordCloud({ productId }: ImageWordCloudProps) {
  const [activeTab, setActiveTab] = useState('positive');

  const { data: clouds, isLoading, error } = useQuery({
    queryKey: ['wordcloud', productId],
    queryFn: () => getWordCloud(productId!),
    enabled: !!productId,
    staleTime: 1000 * 60 * 5 // Cache for 5 mins
  });

  if (!productId) {
    return (
      <Card className="glass-card border-border/50 h-[400px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5 text-primary" />
            Word Cloud
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px] text-muted-foreground">
           Please select a product to view word cloud.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card border-border/50 h-[450px]">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cloud className="h-5 w-5 text-primary" />
            Sentiment Word Cloud
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center h-[300px]">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
            <div className="flex flex-col items-center justify-center h-[300px] text-red-400">
                <AlertCircle className="h-8 w-8 mb-2" />
                <p>Failed to load word cloud</p>
            </div>
        ) : (
          <Tabs defaultValue="positive" value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="positive">Positive</TabsTrigger>
              <TabsTrigger value="neutral">Neutral</TabsTrigger>
              <TabsTrigger value="negative">Negative</TabsTrigger>
            </TabsList>
            
            {['positive', 'neutral', 'negative'].map((sentiment) => (
                <TabsContent key={sentiment} value={sentiment} className="mt-4">
                    <div className="relative w-full h-[300px] bg-white/5 rounded-lg overflow-hidden flex items-center justify-center border border-white/10">
                        {clouds?.[sentiment as keyof typeof clouds] ? (
                            <img 
                                src={clouds[sentiment as keyof typeof clouds]} 
                                alt={`${sentiment} word cloud`} 
                                className="max-w-full max-h-full object-contain"
                            />
                        ) : (
                            <p className="text-muted-foreground">No data for {sentiment} sentiment.</p>
                        )}
                    </div>
                </TabsContent>
            ))}
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
