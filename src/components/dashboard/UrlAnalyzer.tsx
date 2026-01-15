import React, { useState } from 'react';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

interface Props {
  products: { id: string; name: string }[];
}

export default function UrlAnalyzer({ products }: Props) {
  const [url, setUrl] = useState('');
  const [pid, setPid] = useState<string | null>(null);

  const handleScan = async () => {
    if (!url) { toast.error('Paste a YouTube or Reddit link first'); return; }
    try {
      toast.promise(apiClient.post('/api/analyze/url', { url, product_name: products.find(p => p.id === pid)?.name }), {
        loading: 'Starting scan...',
        success: 'Scan started',
        error: 'Failed to start scan'
      });
    } catch (e: any) {
      toast.error(e.message || 'Scan failed');
    }
  };

  return (
    <div className="flex gap-3 items-center">
      <Input placeholder="Paste YouTube or Reddit Link" value={url} onChange={(e) => setUrl(e.target.value)} className="flex-1" />

      <Select value={pid || ''} onValueChange={(v) => setPid(v || null)}>
        <SelectTrigger className="w-56">
          <SelectValue placeholder="Optional product" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="">None</SelectItem>
          {products.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
        </SelectContent>
      </Select>

      <Button className="bg-sentinel-credibility hover:bg-sentinel-credibility/90" onClick={handleScan}>Scan Now</Button>
    </div>
  );
}
import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const UrlAnalyzer: React.FC = () => {
  const [url, setUrl] = useState('');
  const [productName, setProductName] = useState('');
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  const handleScan = async () => {
    if (!url || url.trim().length === 0) {
      toast.error('Please paste a YouTube or Reddit link first');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/analyze/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, product_name: productName || undefined })
      });

      const j = await res.json();
      if (!res.ok) {
        toast.error(j.detail || j.message || 'Failed to analyze URL');
        setLoading(false);
        return;
      }

      const added = j.data?.reviews_added ?? 0;
      const platform = j.data?.platform ?? 'resource';
      toast.success(`Scraped ${added} comments from ${platform.charAt(0).toUpperCase() + platform.slice(1)}!`);

      // Refresh dashboard data
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setUrl('');
      setProductName('');
    } catch (e) {
      toast.error('Error scanning URL: ' + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full p-4 rounded-md border border-input bg-background">
      <div className="flex flex-col md:flex-row gap-2">
        <div className="flex-1">
          <Input placeholder="Paste YouTube or Reddit Link" value={url} onChange={e => setUrl(e.target.value)} />
        </div>
        <div className="w-48">
          <Input placeholder="Optional product name" value={productName} onChange={e => setProductName(e.target.value)} />
        </div>
        <div className="w-36">
          <Button onClick={handleScan} disabled={loading}>
            {loading ? 'Scanning…' : 'Scan Now'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UrlAnalyzer;
