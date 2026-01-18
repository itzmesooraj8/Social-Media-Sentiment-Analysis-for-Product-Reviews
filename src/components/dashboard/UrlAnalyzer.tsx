import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Youtube, Search } from "lucide-react";
import { sentinelApi } from '@/lib/api';
import { useToast } from "@/hooks/use-toast";

interface UrlAnalyzerProps {
  onAnalysisComplete?: () => void;
  selectedProductId?: string; // Optional: Link to a specific product
}

export const UrlAnalyzer: React.FC<UrlAnalyzerProps> = ({ onAnalysisComplete, selectedProductId }) => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!url.trim()) return;

    setIsLoading(true);
    try {
      // 1. Send URL/Query to Backend
      const result = await sentinelApi.scrapeYoutube(url, selectedProductId);

      // 2. Success Feedback
      toast({
        title: "Analysis Complete",
        description: `Successfully analyzed ${result.saved || result.count} comments from YouTube.`,
        variant: "default",
      });

      setUrl('');

      // 3. Refresh Dashboard Data
      if (onAnalysisComplete) {
        onAnalysisComplete();
      }

    } catch (error: any) {
      console.error(error);
      toast({
        title: "Analysis Failed",
        description: error.response?.data?.detail || "Could not fetch YouTube data. Check API Key.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Youtube className="h-5 w-5 text-red-600" />
          Live YouTube Analyzer
        </CardTitle>
        <CardDescription>
          Paste a video URL or search query to analyze real-time comments.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Input
            placeholder="https://youtube.com/watch?v=... or 'iPhone 15 Review'"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <Button
            onClick={handleAnalyze}
            disabled={isLoading || !url}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
