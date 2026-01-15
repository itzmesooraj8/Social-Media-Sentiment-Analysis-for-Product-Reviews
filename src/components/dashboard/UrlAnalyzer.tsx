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
