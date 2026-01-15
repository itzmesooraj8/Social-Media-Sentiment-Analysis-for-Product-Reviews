import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { getProducts, createProduct, deleteProduct, scrapeReddit } from '@/lib/api';
import apiClient from '@/lib/api'; // Direct access for custom endpoints like YouTube if needed
import {
  Package,
  Plus,
  Search,
  MoreVertical,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Star,
  Eye,
  Edit2,
  Trash2,
  ExternalLink,
  Download
} from 'lucide-react';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface Product {
  id: string;
  name: string;
  sku: string;
  category: string;
  totalReviews: number;
  sentimentScore: number;
  sentimentTrend: 'up' | 'down' | 'stable';
  credibilityScore: number;
  lastAnalyzed: Date;
  status: 'active' | 'paused' | 'archived';
  platforms: string[];
}

// Mock data removed. Usage strictly from API.

const Products = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');

  // Dialog States
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({
    name: '',
    sku: '',
    category: '',
    description: '',
    keywords: ''
  });

  // Import Dialog State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importingProductId, setImportingProductId] = useState<string | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);

  // YouTube Scrape Dialog State
  const [isYouTubeDialogOpen, setIsYouTubeDialogOpen] = useState(false);
  const [youtubeQuery, setYoutubeQuery] = useState('');
  const [youtubeScrapePid, setYoutubeScrapePid] = useState<string | null>(null);
  
  // URL Analyzer state (for Direct URL Analysis feature)
  const [analyzerUrl, setAnalyzerUrl] = useState('');
  const [analyzerProductId, setAnalyzerProductId] = useState<string | null>(null);
  const [analyzerProductName, setAnalyzerProductName] = useState('');

  // --- Queries ---

  const { data: productsData, isLoading } = useQuery<Product[]>({
    queryKey: ['products'],
    queryFn: async () => {
      const res = await getProducts();
      if (!res.success) throw new Error(res.message);
      // Transform API data to UI model
      return res.data.map((p: any) => ({
        id: p.id,
        name: p.name,
        sku: p.sku,
        category: p.category,
        totalReviews: 0, // Backend doesn't return counts yet
        sentimentScore: 0,
        sentimentTrend: 'stable',
        credibilityScore: 0,
        lastAnalyzed: new Date(p.created_at || Date.now()),
        status: p.status,
        platforms: ['reddit', 'youtube']
      }));
    }
  });

  const products = productsData || [];

  // --- Mutations ---

  const addProductMutation = useMutation({
    mutationFn: async (data: typeof newProduct) => {
      const payload = {
        ...data,
        keywords: data.keywords.split(',').map(k => k.trim())
      };
      return await createProduct(payload);
    },
    onSuccess: () => {
      toast.success('Product created successfully');
      setIsAddDialogOpen(false);
      setNewProduct({ name: '', sku: '', category: '', description: '', keywords: '' });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => {
      toast.error(`Failed to create product: ${err.message || 'Unknown error'}`);
    }
  });

  const scrapeRedditMutation = useMutation({
    mutationFn: async ({ id, name }: { id: string, name: string }) => {
      return await scrapeReddit(id, name);
    },
    onSuccess: (data) => {
      toast.success(`Scraped ${data.count} reviews from Reddit!`);
    },
    onError: (err: any) => {
      toast.error(`Reddit scrape failed: ${err.message}`);
    }
  });

  const scrapeYouTubeMutation = useMutation({
    mutationFn: async ({ pid, query }: { pid: string, query: string }) => {
      const res = await apiClient.post(`/api/scrape/youtube`, null, {
        params: { product_id: pid, query: query }
      });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      setIsYouTubeDialogOpen(false);
      // Invalidate products to update timestamps/counts if we had them
      queryClient.invalidateQueries({ queryKey: ['products'] });
      // Also dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (err: any) => {
      toast.error(`YouTube scrape failed: ${err.message}`);
    }
  });

  const analyzeUrlMutation = useMutation({
    mutationFn: async ({ url, product_name }: { url: string, product_name?: string }) => {
      const payload = { url, product_name };
      const res = await apiClient.post('/api/analyze/url', payload);
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(data?.message || 'URL analysis started');
      // refresh dashboard and products
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => {
      toast.error(`URL analysis failed: ${err.message || err}`);
    }
  });

  const importCsvMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      // apiClient interceptor handles Auth
      const response = await apiClient.post('/api/import/csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Dataset imported successfully!');
      setIsImportDialogOpen(false);
      setImportFile(null);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (err: any) => {
      toast.error(`Import failed: ${err.message}`);
    }
  });


  // --- Event Handlers ---

  const handleAddProduct = () => {
    if (!newProduct.name || !newProduct.sku) {
      toast.error("Name and SKU are required");
      return;
    }
    addProductMutation.mutate(newProduct);
  };

  const handleImportSubmit = () => {
    if (!importFile || !importingProductId) {
      toast.error("Please select a file and a product.");
      return;
    }
    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('product_id', importingProductId);
    formData.append('platform', 'twitter');

    toast.promise(importCsvMutation.mutateAsync(formData), {
      loading: 'Uploading...',
      success: 'Imported!',
      error: 'Failed'
    });
  };

  const handleScrapeReddit = (product: Product) => {
    toast.promise(scrapeRedditMutation.mutateAsync({ id: product.id, name: product.name }), {
      loading: 'Scraping Reddit...',
      success: (d) => `Got ${d.count} reviews`,
      error: (e) => e.message
    });
  };

  const handleYouTubeSubmit = () => {
    if (!youtubeScrapePid || !youtubeQuery) return;
    toast.promise(scrapeYouTubeMutation.mutateAsync({ pid: youtubeScrapePid, query: youtubeQuery }), {
      loading: 'Searching YouTube...',
      success: 'Started analysis!',
      error: (e) => e.message
    });
  };


  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category.toLowerCase().includes(searchQuery.toLowerCase())
  );




  const formatLastAnalyzed = (date: Date) => {
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 60) return `${minutes}m ago`;
    return `${hours}h ago`;
  };

  const statusStyles = {
    active: 'bg-sentinel-positive/10 text-sentinel-positive border-sentinel-positive/30',
    paused: 'bg-sentinel-warning/10 text-sentinel-warning border-sentinel-warning/30',
    archived: 'bg-muted text-muted-foreground border-border',
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Products</h1>
            <p className="text-muted-foreground">Manage and monitor your product sentiment analysis</p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setImportingProductId(null); // Reset for manual selection
                setIsImportDialogOpen(true);
              }}
            >
              <Download className="h-4 w-4 mr-2 rotate-180" />
              Import Dataset
            </Button>

            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Product
                </Button>
              </DialogTrigger>
              <DialogContent className="glass-card border-border/50">
                <DialogHeader>
                  <DialogTitle>Add New Product</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Product Name</Label>
                    <Input placeholder="Enter product name" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>SKU</Label>
                      <Input placeholder="SKU-12345" />
                    </div>
                    <div className="space-y-2">
                      <Label>Category</Label>
                      <Input placeholder="Electronics" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea placeholder="Brief product description..." />
                  </div>
                  <div className="space-y-2">
                    <Label>Keywords to Track</Label>
                    <Input placeholder="keyword1, keyword2, keyword3" />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button variant="outline" className="flex-1" onClick={() => setIsAddDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button className="flex-1 bg-sentinel-credibility hover:bg-sentinel-credibility/90" onClick={handleAddProduct} disabled={addProductMutation.status === 'pending'}>
                      {addProductMutation.status === 'pending' ? 'Adding...' : 'Add Product'}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Import Dialog */}
          <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
            <DialogContent className="glass-card border-border/50">
              <DialogHeader>
                <DialogTitle>Import Dataset (CSV)</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Select Product</Label>
                  <Select
                    value={importingProductId || ""}
                    onValueChange={setImportingProductId}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a product..." />
                    </SelectTrigger>
                    <SelectContent>
                      {products.map(p => (
                        <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Select CSV File</Label>
                  <Input
                    type="file"
                    accept=".csv,.txt"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="cursor-pointer"
                  />
                  <p className="text-xs text-muted-foreground">
                    Required columns: 'text' or 'content'. Optional: 'author', 'date'.
                  </p>
                </div>
                <div className="flex gap-2 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => setIsImportDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    disabled={!importFile || !importingProductId}
                    onClick={handleImportSubmit}
                    className="flex-1 bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                    Upload & Analyze
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* YouTube Scrape Dialog */}
          <Dialog open={isYouTubeDialogOpen} onOpenChange={setIsYouTubeDialogOpen}>
            <DialogContent className="glass-card border-border/50">
              <DialogHeader>
                <DialogTitle>Scrape YouTube</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>YouTube Video URL or Search Query</Label>
                  <Input
                    value={youtubeQuery}
                    onChange={(e) => setYoutubeQuery(e.target.value)}
                    placeholder="https://youtu.be/... or Product Review"
                  />
                  <p className="text-xs text-muted-foreground">
                    Paste a specific video link for best results.
                  </p>
                </div>
                <div className="flex gap-2 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => setIsYouTubeDialogOpen(false)}>Cancel</Button>
                  <Button
                    disabled={!youtubeQuery}
                    onClick={handleYouTubeSubmit}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white">
                    Start Scraping
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search & Stats */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search products by name or SKU..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex gap-4">
            <div className="glass-card px-4 py-2 flex items-center gap-2">
              <Package className="h-4 w-4 text-sentinel-credibility" />
              <span className="text-sm font-medium">{products.length} Products</span>
            </div>
            <div className="glass-card px-4 py-2 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-sentinel-positive" />
              <span className="text-sm font-medium">32.4K Reviews</span>
            </div>
          </div>
        </div>

        {/* URL Analyzer (Direct URL Analysis) */}
        <div className="glass-card p-4 flex items-center gap-3">
          <Input
            placeholder="Paste YouTube or Reddit Link"
            value={analyzerUrl}
            onChange={(e) => setAnalyzerUrl(e.target.value)}
            className="flex-1"
          />

          <Select value={analyzerProductId || ''} onValueChange={(v) => {
            setAnalyzerProductId(v || null);
            const p = products.find(x => x.id === v);
            setAnalyzerProductName(p ? p.name : '');
          }}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Optional product" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None</SelectItem>
              {products.map(p => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            onClick={() => {
              if (!analyzerUrl) { toast.error('Please paste a YouTube or Reddit link first'); return; }
              const product_name = analyzerProductName || undefined;
              toast.promise(analyzeUrlMutation.mutateAsync({ url: analyzerUrl, product_name }), {
                loading: 'Starting analysis...',
                success: 'Analysis started',
                error: 'Failed to start analysis'
              });
            }}
            className="bg-sentinel-credibility hover:bg-sentinel-credibility/90"
          >
            Scan Now
          </Button>
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredProducts.map((product, index) => (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className="glass-card p-5 hover:border-sentinel-credibility/30 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold truncate">{product.name}</h3>
                    <Badge
                      variant="outline"
                      className={cn('text-xs capitalize', statusStyles[product.status])}
                    >
                      {product.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span>{product.sku}</span>
                    <span>•</span>
                    <span>{product.category}</span>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="glass-card border-border/50">
                    <DropdownMenuItem>
                      <Eye className="h-4 w-4 mr-2" />
                      View Dashboard
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Edit2 className="h-4 w-4 mr-2" />
                      Edit Product
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Sources
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => handleScrapeReddit(product)}
                      disabled={scrapeRedditMutation.status === 'pending'}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      {scrapeRedditMutation.status === 'pending' ? 'Scraping...' : 'Scrape Reddit Reviews'}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => {
                        setYoutubeScrapePid(product.id);
                        setYoutubeQuery(product.name);
                        setIsYouTubeDialogOpen(true);
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Scrape YouTube Reviews
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => {
                        setImportingProductId(product.id);
                        setIsImportDialogOpen(true);
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Import CSV Dataset (Twitter/X)
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-sentinel-negative">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Reviews</p>
                  <p className="font-semibold">{product.totalReviews.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Sentiment</p>
                  <div className="flex items-center gap-1">
                    <span className={cn(
                      'font-semibold',
                      product.sentimentScore >= 70 ? 'text-sentinel-positive' :
                        product.sentimentScore >= 50 ? 'text-sentinel-warning' : 'text-sentinel-negative'
                    )}>
                      {product.sentimentScore}%
                    </span>
                    {product.sentimentTrend === 'up' && <TrendingUp className="h-3 w-3 text-sentinel-positive" />}
                    {product.sentimentTrend === 'down' && <TrendingDown className="h-3 w-3 text-sentinel-negative" />}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Credibility</p>
                  <p className="font-semibold text-sentinel-credibility">{product.credibilityScore}%</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">Sentiment Score</span>
                  <span className="text-xs text-muted-foreground">{product.sentimentScore}%</span>
                </div>
                <Progress value={product.sentimentScore} className="h-1.5" />
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-border/50">
                <div className="flex items-center gap-1">
                  {product.platforms.map(platform => (
                    <div
                      key={platform}
                      className="w-6 h-6 rounded bg-muted flex items-center justify-center"
                      title={platform}
                    >
                      <span className="text-xs capitalize">{platform[0]}</span>
                    </div>
                  ))}
                </div>
                <span className="text-xs text-muted-foreground">
                  Updated {formatLastAnalyzed(product.lastAnalyzed)}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Products;
