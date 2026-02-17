import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Youtube, Search } from "lucide-react";
import { sentinelApi, getYoutubeStreamUrl } from '@/lib/api';
import { useToast } from "@/hooks/use-toast";

interface UrlAnalyzerProps {
  onAnalysisComplete?: () => void;
  selectedProductId?: string; // Optional: Link to a specific product
}

export const UrlAnalyzer: React.FC<UrlAnalyzerProps> = ({ onAnalysisComplete, selectedProductId }) => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showProductForm, setShowProductForm] = useState(false);
  const [productName, setProductName] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const { toast } = useToast();

  const handleAnalyze = () => {
    if (!url.trim()) return;
    setShowProductForm(true);
  };

  const handleSubmitProduct = async () => {
    if (!productName.trim()) {
      toast({ title: 'Missing name', description: 'Please enter a product name.', variant: 'destructive' });
      return;
    }

    setIsLoading(true);
    try {
      // 1. Create product in Supabase
      const createResp = await sentinelApi.createProduct({ name: productName, keywords: [], track_youtube: true });
      let product: any = null;
      if (createResp?.data) {
        product = Array.isArray(createResp.data) ? createResp.data[0] : createResp.data;
      } else {
        product = Array.isArray(createResp) ? createResp[0] : createResp;
      }
      const productId = product?.id || product?.[0]?.id;

      // 2. Open SSE connection to get real-time comments
      // Use helper from api.ts to correctly handle base URL overrides
      const streamUrl = getYoutubeStreamUrl(url, productId, 100);

      const es = new EventSource(streamUrl);
      es.onmessage = (ev) => {
        try {
          const payload = JSON.parse(ev.data);
          if (payload?.type === 'comment' && payload.comment) {
            setResults((prev) => [payload.comment, ...prev]);
          }
        } catch (err) {
          // ignore parse errors
        }
      };
      es.addEventListener('done', () => {
        toast({ title: 'Analysis Complete', description: `Streaming finished. Showing ${results.length} items.`, variant: 'default' });
        es.close();
        setIsLoading(false);
        setShowProductForm(false);
        setProductName('');
        if (onAnalysisComplete) onAnalysisComplete();
      });
      es.onerror = (err) => {
        console.error('SSE error', err);
        toast({ title: 'Stream Error', description: 'Connection lost. Some results may be missing.', variant: 'destructive' });
        es.close();
        setIsLoading(false);
      };

    } catch (error: any) {
      console.error(error);
      toast({ title: 'Analysis Failed', description: error.response?.data?.detail || 'Could not fetch YouTube data. Check API Key.', variant: 'destructive' });
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

        {showProductForm && (
          <div className="mt-4 p-4 border rounded bg-surface">
            <h3 className="text-sm font-semibold mb-2">Product details</h3>
            <div className="flex gap-2">
              <Input
                placeholder="Product name"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitProduct()}
              />
              <Button onClick={handleSubmitProduct} disabled={isLoading || !productName} className="bg-green-600 hover:bg-green-700 text-white">Create & Analyze</Button>
              <Button onClick={() => setShowProductForm(false)} variant="ghost">Cancel</Button>
            </div>
          </div>
        )}

        {results && results.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-2">Latest analysis results</h4>
            <div className="grid gap-2">
              {results.map((r, idx) => (
                <div key={idx} className="p-3 rounded border bg-muted">
                  <div className="text-sm">{r.content || r.text || r.body}</div>
                  <div className="text-xs text-muted-foreground mt-1">{r.author ? `by ${r.author}` : r.source_url}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
