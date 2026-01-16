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
      toast({ title: "Error", description: "Please paste a valid URL", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/api/analyze/url', { url });
      toast({ 
        title: "Analysis Complete", 
        description: `Successfully ingested ${res.count} reviews from ${res.platform}.` 
      });
      setTimeout(() => window.location.reload(), 1500); // Auto-refresh data
    } catch (e) {
      toast({ title: "Analysis Failed", description: "Could not scrape URL.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full p-6 bg-card border rounded-xl shadow-sm mb-8">
      <div className="flex items-center gap-2 mb-4">
        <LinkIcon className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-lg">Real-Time URL Intelligence</h3>
      </div>
      <div className="flex gap-3">
        <Input 
          placeholder="Paste YouTube or Reddit Link..." 
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="h-12"
        />
        <Button onClick={handleAnalyze} disabled={loading} size="lg" className="h-12">
          {loading ? <Loader2 className="animate-spin" /> : <Search />} Analyze
        </Button>
      </div>
    </div>
  );
}
