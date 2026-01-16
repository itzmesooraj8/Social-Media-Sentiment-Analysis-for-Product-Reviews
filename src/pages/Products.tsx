import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { getProducts, createProduct, updateProduct, deleteProduct, scrapeReddit } from '@/lib/api';
import apiClient from '@/lib/api';
import {
  Package,
  Plus,
  Search,
  MoreVertical,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Edit2,
  Trash2,
  ExternalLink,
  Download,
  AlertCircle,
  Link,
  CheckCircle2,
  Eye
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
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

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

const Products = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  // --- States ---

  // Add Dialog
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({
    name: '',
    sku: '',
    category: '',
    description: '',
    keywords: ''
  });

  // Edit Dialog
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  // Import Dialog
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importingProductId, setImportingProductId] = useState<string | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);

  // YouTube Scrape Dialog
  const [isYouTubeDialogOpen, setIsYouTubeDialogOpen] = useState(false);
  const [youtubeQuery, setYoutubeQuery] = useState('');
  const [youtubeScrapePid, setYoutubeScrapePid] = useState<string | null>(null);

  // Analyzer Dialog (Smart Scan)
  const [isAnalyzerDialogOpen, setIsAnalyzerDialogOpen] = useState(false);
  const [analyzerUrl, setAnalyzerUrl] = useState('');
  const [analyzerMode, setAnalyzerMode] = useState<'existing' | 'new'>('existing');
  const [analyzerSelectedPid, setAnalyzerSelectedPid] = useState<string | null>(null);
  const [analyzerNewProduct, setAnalyzerNewProduct] = useState({ name: '', category: '' });

  // --- Queries ---

  const { data: productsData, isLoading } = useQuery<Product[]>({
    queryKey: ['products'],
    queryFn: async () => {
      const data = await getProducts();
      return data.map((p: any) => ({
        id: p.id,
        name: p.name,
        sku: p.sku,
        category: p.category,
        totalReviews: 0,
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
      // Just creating product
      const payload = { ...data, keywords: data.keywords.split(',').map(k => k.trim()) };
      return await createProduct(payload);
    },
    onSuccess: (data) => {
      toast.success('Product created successfully');
      setIsAddDialogOpen(false);
      setNewProduct({ name: '', sku: '', category: '', description: '', keywords: '' });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => toast.error(err.message)
  });

  const updateProductMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string, data: Partial<Product> }) => {
      return await updateProduct(id, data);
    },
    onSuccess: () => {
      toast.success('Product updated');
      setEditingProduct(null);
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => toast.error(err.message)
  });

  const deleteProductMutation = useMutation({
    mutationFn: async (id: string) => {
      return await deleteProduct(id);
    },
    onSuccess: () => {
      toast.success('Product deleted');
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => toast.error(err.message)
  });

  const analyzeUrlMutation = useMutation({
    mutationFn: async (payload: { url: string, product_id?: string, new_product_name?: string, new_product_category?: string }) => {
      let pid = payload.product_id;

      if (!pid && payload.new_product_name) {
        const newP = await createProduct({
          name: payload.new_product_name,
          category: payload.new_product_category || 'General',
          sku: `AUTO-${Date.now().toString().slice(-6)}`
        });
        pid = newP.id;
      }

      const res = await apiClient.post('/analyze/url', {
        url: payload.url,
        product_id: pid
      });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success('Analysis started successfully!');
      setIsAnalyzerDialogOpen(false);
      setAnalyzerUrl(''); // clear url
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => toast.error(`Analysis failed: ${err.message}`)
  });

  const scrapeRedditMutation = useMutation({
    mutationFn: async ({ id, name }: { id: string, name: string }) => {
      return await scrapeReddit(name);
    },
    onSuccess: (data) => toast.success(`Scraped ${data.count} reviews from Reddit!`),
    onError: (err: any) => toast.error(err.message)
  });

  const scrapeYouTubeMutation = useMutation({
    mutationFn: async ({ pid, query }: { pid: string, query: string }) => {
      const res = await apiClient.post(`/scrape/youtube`, null, { params: { product_id: pid, query } });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      setIsYouTubeDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (err: any) => toast.error(err.message)
  });

  const importCsvMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await apiClient.post('/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Dataset imported!');
      setIsImportDialogOpen(false);
      setImportFile(null);
    },
    onError: (err: any) => toast.error(err.message)
  });


  // --- Event Handlers ---

  const handleScanNowClick = () => {
    if (!analyzerUrl) {
      toast.error("Please enter a URL first");
      return;
    }
    setIsAnalyzerDialogOpen(true);
  };

  const handleAnalyzerSubmit = () => {
    if (analyzerMode === 'existing' && !analyzerSelectedPid) {
      toast.error("Please select a product");
      return;
    }
    if (analyzerMode === 'new' && !analyzerNewProduct.name) {
      toast.error("Please enter a product name");
      return;
    }

    analyzeUrlMutation.mutate({
      url: analyzerUrl,
      product_id: analyzerSelectedPid || undefined,
      new_product_name: analyzerMode === 'new' ? analyzerNewProduct.name : undefined,
      new_product_category: analyzerMode === 'new' ? analyzerNewProduct.category : undefined,
    });
  };

  const handleImportSubmit = () => {
    if (!importFile || !importingProductId) {
      toast.error("Please select a file and a product.");
      return;
    }
    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('product_id', importingProductId);
    formData.append('platform', 'twitter'); // Defaulting to generic/twitter for text
    importCsvMutation.mutate(formData);
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchQuery.toLowerCase())
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

        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Products</h1>
            <p className="text-muted-foreground">Manage and monitor your product sentiment analysis</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => { setImportingProductId(null); setIsImportDialogOpen(true); }}>
              <Download className="h-4 w-4 mr-2 rotate-180" />
              Import Dataset
            </Button>
            <Button className="bg-sentinel-credibility hover:bg-sentinel-credibility/90" onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </Button>
          </div>
        </div>

        {/* --- Dialogs --- */}

        {/* 1. Add Product Dialog */}
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogContent className="glass-card border-border/50">
            <DialogHeader>
              <DialogTitle>Add New Product</DialogTitle>
              <DialogDescription>Enter details to track a new product.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label>Product Name</Label>
                <Input placeholder="e.g. iPhone 16" value={newProduct.name} onChange={e => setNewProduct({ ...newProduct, name: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>SKU</Label>
                  <Input placeholder="SKU-123" value={newProduct.sku} onChange={e => setNewProduct({ ...newProduct, sku: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Input placeholder="Electronics" value={newProduct.category} onChange={e => setNewProduct({ ...newProduct, category: e.target.value })} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea value={newProduct.description} onChange={e => setNewProduct({ ...newProduct, description: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Keywords (comma separated)</Label>
                <Input placeholder="phone, apple, 5g" value={newProduct.keywords} onChange={e => setNewProduct({ ...newProduct, keywords: e.target.value })} />
              </div>
              <Button className="w-full bg-sentinel-credibility" onClick={() => addProductMutation.mutate(newProduct)}>Create Product</Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* 2. Edit Product Dialog */}
        <Dialog open={!!editingProduct} onOpenChange={(open) => !open && setEditingProduct(null)}>
          <DialogContent className="glass-card border-border/50">
            <DialogHeader>
              <DialogTitle>Edit Product</DialogTitle>
              <DialogDescription>Modify product details.</DialogDescription>
            </DialogHeader>
            {editingProduct && (
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Product Name</Label>
                  <Input value={editingProduct.name} onChange={e => setEditingProduct({ ...editingProduct, name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Input value={editingProduct.category} onChange={e => setEditingProduct({ ...editingProduct, category: e.target.value })} />
                </div>
                <Button className="w-full bg-sentinel-credibility" onClick={() => updateProductMutation.mutate({ id: editingProduct.id, data: editingProduct })}>Save Changes</Button>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* 3. Analyzer Wizard Dialog (Smart Scan) */}
        <Dialog open={isAnalyzerDialogOpen} onOpenChange={setIsAnalyzerDialogOpen}>
          <DialogContent className="glass-card border-border/50 sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Analyze Source</DialogTitle>
              <DialogDescription>
                Configure how this URL should be analyzed.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6 pt-2">
              <div className="space-y-2">
                <Label>Source URL</Label>
                <div className="flex items-center gap-2 p-2 rounded-md bg-muted/50 border border-border/50 text-sm break-all">
                  <Link className="h-4 w-4 shrink-0 text-sentinel-credibility" />
                  {analyzerUrl}
                </div>
              </div>

              <Tabs value={analyzerMode} onValueChange={(v: any) => setAnalyzerMode(v)} className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="existing">Existing Product</TabsTrigger>
                  <TabsTrigger value="new">New Product</TabsTrigger>
                </TabsList>

                <TabsContent value="existing" className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Select Product</Label>
                    <Select value={analyzerSelectedPid || '_none_'} onValueChange={(v) => setAnalyzerSelectedPid(v === '_none_' ? null : v)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a product..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="_none_">Select a product</SelectItem>
                        {products.map(p => (
                          <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>

                <TabsContent value="new" className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Product Name</Label>
                    <Input placeholder="e.g. Samsung S24" value={analyzerNewProduct.name} onChange={e => setAnalyzerNewProduct({ ...analyzerNewProduct, name: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Input placeholder="Electronics" value={analyzerNewProduct.category} onChange={e => setAnalyzerNewProduct({ ...analyzerNewProduct, category: e.target.value })} />
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAnalyzerDialogOpen(false)}>Cancel</Button>
                <Button className="bg-sentinel-credibility" onClick={handleAnalyzerSubmit}>
                  {analyzeUrlMutation.status === 'pending' ? 'Starting...' : 'Start Analysis'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>

        {/* 4. Import Dialog */}
        <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
          <DialogContent className="glass-card border-border/50">
            <DialogHeader>
              <DialogTitle>Import Dataset</DialogTitle>
              <DialogDescription>Upload a CSV file containing reviews.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label>Product</Label>
                <Select value={importingProductId || ""} onValueChange={setImportingProductId}>
                  <SelectTrigger><SelectValue placeholder="Choose..." /></SelectTrigger>
                  <SelectContent>{products.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>File (CSV)</Label>
                <Input type="file" accept=".csv" onChange={e => setImportFile(e.target.files?.[0] || null)} />
              </div>
              <Button onClick={handleImportSubmit}>Upload</Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* 5. YouTube Dialog */}
        <Dialog open={isYouTubeDialogOpen} onOpenChange={setIsYouTubeDialogOpen}>
          <DialogContent className="glass-card border-border/50">
            <DialogHeader>
              <DialogTitle>Scrape YouTube</DialogTitle>
              <DialogDescription>Enter a query or URL to scrape video comments.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <Input placeholder="Search Query / URL" value={youtubeQuery} onChange={e => setYoutubeQuery(e.target.value)} />
              <Button className="bg-red-600 hover:bg-red-700 w-full" onClick={() => scrapeYouTubeMutation.mutate({ pid: youtubeScrapePid!, query: youtubeQuery })}>Scrape</Button>
            </div>
          </DialogContent>
        </Dialog>


        {/* --- Main Content --- */}

        {/* Scan Bar */}
        <div className="glass-card p-4 flex items-center gap-3">
          <Input
            placeholder="Paste YouTube or Reddit Link to scan..."
            value={analyzerUrl}
            onChange={e => setAnalyzerUrl(e.target.value)}
            className="flex-1"
          />
          <Button onClick={handleScanNowClick} className="bg-sentinel-credibility w-32">
            Scan Now
          </Button>
        </div>

        {/* Product Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredProducts.map((product, index) => (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass-card p-5 hover:border-sentinel-credibility/30 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold truncate text-lg">{product.name}</h3>
                    <Badge variant="outline" className={cn('text-xs capitalize', statusStyles[product.status])}>{product.status}</Badge>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">{product.sku} • {product.category}</div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8"><MoreVertical className="h-4 w-4" /></Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="glass-card border-border/50">
                    <DropdownMenuItem onClick={() => navigate(`/dashboard`)}>
                      <BarChart3 className="h-4 w-4 mr-2" /> View Dashboard
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setEditingProduct(product)}>
                      <Edit2 className="h-4 w-4 mr-2" /> Edit Product
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate(`/analytics`)}>
                      <ExternalLink className="h-4 w-4 mr-2" /> View Sources
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => scrapeRedditMutation.mutate({ id: product.id, name: product.name })}>
                      <Download className="h-4 w-4 mr-2" /> Scrape Reddit Reviews
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setYoutubeScrapePid(product.id); setYoutubeQuery(product.name); setIsYouTubeDialogOpen(true); }}>
                      <Download className="h-4 w-4 mr-2" /> Scrape YouTube Reviews
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setImportingProductId(product.id); setIsImportDialogOpen(true); }}>
                      <Download className="h-4 w-4 mr-2" /> Import CSV Dataset
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-sentinel-negative" onClick={() => {
                      if (confirm('Are you sure you want to delete this product?')) {
                        deleteProductMutation.mutate(product.id);
                      }
                    }}>
                      <Trash2 className="h-4 w-4 mr-2" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div><p className="text-xs text-muted-foreground mb-1">Reviews</p><p className="font-semibold">{product.totalReviews}</p></div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Sentiment</p>
                  <div className="flex items-center gap-1">
                    <span className={cn('font-semibold', product.sentimentScore >= 70 ? 'text-sentinel-positive' : 'text-sentinel-negative')}>
                      {product.sentimentScore}%
                    </span>
                  </div>
                </div>
                <div><p className="text-xs text-muted-foreground mb-1">Credibility</p><p className="font-semibold text-sentinel-credibility">{product.credibilityScore}%</p></div>
              </div>

              <Progress value={product.sentimentScore} className="h-1.5 mb-3" />

              <div className="flex items-center justify-between pt-3 border-t border-border/50 text-xs text-muted-foreground">
                <div className="flex gap-1">{product.platforms.map(p => <span key={p} className="capitalize">{p}, </span>)}</div>
                <span>Updated just now</span>
              </div>

            </motion.div>
          ))}
        </div>

      </div>
    </DashboardLayout>
  );
};

export default Products;
