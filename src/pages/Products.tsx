import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
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
  // Fetch products from API
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [scrapingProductId, setScrapingProductId] = useState<string | null>(null);
  const [newProduct, setNewProduct] = useState({
    name: '',
    sku: '',
    category: '',
    description: '',
    keywords: ''
  });

  const [products, setProducts] = useState<Product[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoading, setIsLoading] = useState(true);

  // Import State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [importingProductId, setImportingProductId] = useState<string | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);

  const handleImportSubmit = async () => {
    if (!importFile || !importingProductId) return;

    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('product_id', importingProductId);
    formData.append('platform', 'twitter'); // Default or let user select

    try {
      const response = await fetch('http://localhost:8000/api/import/csv', {
        method: 'POST',
        headers: {
          // Content-Type header must be undefined so browser sets boundary
          "Authorization": `Bearer ${localStorage.getItem("token") || ""}`
        },
        body: formData
      });
      const data = await response.json();
      if (data.success) {
        alert(data.data.message);
        setIsImportDialogOpen(false);
        setImportFile(null);
      } else {
        alert("Import failed: " + (data.message || data.detail));
      }
    } catch (e) {
      console.error(e);
      alert("Import error");
    }
  };

  // Fetch data
  const fetchProducts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/products');
      const data = await response.json();
      if (data.success) {
        // Transform API data to UI model
        const mapped = data.data.map((p: any) => ({
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
          platforms: ['reddit'] // Default
        }));
        setProducts(mapped);
      }
    } catch (error) {
      console.error("Failed to fetch products", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchProducts();
  }, []);

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
    product.category.toLowerCase().includes(searchQuery.toLowerCase())
  );


  const handleScrapeReddit = async (product: Product) => {
    setScrapingProductId(product.id);
    const promise = async () => {
      const { scrapeReddit } = await import('@/lib/api');
      const result = await scrapeReddit(product.id, product.name);
      if (!result.success) throw new Error(result.message || 'Scraping failed');
      return result;
    };

    toast.promise(promise(), {
      loading: `Scraping Reddit reviews for ${product.name}...`,
      success: (data) => `Successfully scraped ${data.count} reviews!`,
      error: (err) => `Scraping failed: ${err.message}`,
    });

    try {
      await promise();
    } catch (e) {
      // Handled by toast
    } finally {
      setScrapingProductId(null);
    }
  };

  const handleAddProduct = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newProduct,
          keywords: newProduct.keywords.split(',').map(k => k.trim())
        })
      });
      const data = await response.json();
      if (data.success) {
        alert('Product added!');
        setIsAddDialogOpen(false);
        setNewProduct({ name: '', sku: '', category: '', description: '', keywords: '' });
        fetchProducts();
      } else {
        alert('Failed to add product');
      }
    } catch (e) {
      console.error(e);
      alert('Error adding product');
    }
  };

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
                  <Button className="flex-1 bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                    Add Product
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Import Dialog */}
          <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
            <DialogContent className="glass-card border-border/50">
              <DialogHeader>
                <DialogTitle>Import Dataset (CSV)</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
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
                    disabled={!importFile}
                    onClick={handleImportSubmit}
                    className="flex-1 bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                    Upload & Analyze
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
                      disabled={scrapingProductId === product.id}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      {scrapingProductId === product.id ? 'Scraping...' : 'Scrape Reddit Reviews'}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => {
                        setScrapingProductId(product.id);
                        const promise = async () => {
                          const res = await fetch(`http://localhost:8000/api/scrape/youtube?product_id=${product.id}&query=${encodeURIComponent(product.name)}`, {
                            method: "POST",
                            headers: { "Authorization": `Bearer ${localStorage.getItem("token") || ""}` }
                          });
                          const data = await res.json();
                          if (!data.success) throw new Error(data.message);
                          return data;
                        };

                        toast.promise(promise(), {
                          loading: 'Searching YouTube comments...',
                          success: (data) => data.message,
                          error: (err) => `YouTube Scrape Error: ${err.message}`
                        });

                        promise().finally(() => setScrapingProductId(null));
                      }}
                      disabled={scrapingProductId === product.id}
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
