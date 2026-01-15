import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { Search, Loader2, Link as LinkIcon } from 'lucide-react';
import { api } from '@/lib/api';

export default function UrlAnalyzer() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!url) {
      toast({ title: "Validation Error", description: "Please paste a URL first.", variant: "destructive" });
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.post('/api/analyze/url', { url });
      
      toast({ 
        title: "Analysis Complete", 
        description: `Successfully ingested ${res.count || 0} reviews from ${res.platform}. Refreshing...`,
        variant: "default"
      });
      
      // Force a dashboard refresh after 1s
      setTimeout(() => window.location.reload(), 1500);
      
    } catch (e) {
      console.error(e);
      toast({ 
        title: "Analysis Failed", 
        description: "Could not scrape this URL. Ensure it is a public YouTube video or Reddit thread.", 
        variant: "destructive" 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full p-6 bg-card border rounded-xl shadow-sm mb-8">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <LinkIcon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">Live Content Analysis</h3>
            <p className="text-muted-foreground text-sm">Paste a YouTube video or Reddit thread URL to analyze it in real-time.</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <Input 
            placeholder="https://www.youtube.com/watch?v=... or https://reddit.com/r/..." 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 text-base h-12"
          />
          <Button onClick={handleAnalyze} disabled={loading} size="lg" className="h-12 px-8">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze Now
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { Search, Loader2, Link as LinkIcon } from 'lucide-react';
import api from '@/lib/api';

export default function UrlAnalyzer() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!url) {
      toast({ title: 'Validation Error', description: 'Please paste a URL first.', variant: 'destructive' });
      return;
    }
    
    setLoading(true);
    try {
      // Calls the secure backend endpoint
      const res = await api.post('/api/analyze/url', { url });
      const data = res.data || res;
      toast({ 
        title: 'Analysis Complete', 
        description: `Successfully ingested ${data.count || 0} reviews from ${data.platform || 'resource'}. Refreshing dashboard...`,
        variant: 'default'
      });
      
    } catch (e: any) {
      console.error(e);
      toast({ 
        title: 'Analysis Failed', 
        description: 'Could not scrape this URL. Check if the link is public.', 
        variant: 'destructive' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full p-6 bg-card border rounded-xl shadow-sm mb-8">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <LinkIcon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-lg">Live Content Analysis</h3>
            <p className="text-muted-foreground text-sm">Paste a YouTube video or Reddit thread URL to analyze it in real-time.</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <Input 
            placeholder="https://www.youtube.com/watch?v=..." 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 text-base h-12"
          />
          <Button onClick={handleAnalyze} disabled={loading} size="lg" className="h-12 px-8">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Scraping...
              </>
            ) : (
              <>
                <Search className="mr-2 h-4 w-4" />
                Analyze Now
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
