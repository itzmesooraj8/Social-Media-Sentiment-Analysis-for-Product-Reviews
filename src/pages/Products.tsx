import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProducts, createProduct, deleteProduct, scrapeReddit } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Trash2, RefreshCw, ExternalLink, MoreVertical } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from 'react-router-dom';
import { Product } from '@/types/sentinel'; // Import shared type

export default function Products() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: '', description: '', url: '' });

  // Fetch Products
  const { data: products = [], isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    refetchInterval: 5000, // Auto-refresh for status updates
  });

  // Create Product
  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setIsOpen(false);
      setNewProduct({ name: '', description: '', url: '' });
      toast({ title: 'Success', description: 'Product added successfully' });
    },
    onError: () => toast({ title: 'Error', description: 'Failed to create product', variant: 'destructive' })
  });

  // Delete Product
  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast({ title: 'Deleted', description: 'Product removed' });
    },
  });

  // Scrape Request
  const scrapeMutation = useMutation({
    mutationFn: scrapeReddit,
    onSuccess: () => {
      toast({ title: 'Scraping Started', description: 'Checking Reddit for new reviews...' });
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: newProduct.name,
      description: newProduct.description,
      platform: 'generic', // Default
      url: newProduct.url,
      status: 'active'
    });
  };

  if (isLoading) return <div className="flex justify-center p-8">Loading...</div>;

  return (
    <DashboardLayout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Products</h1>
          <p className="text-muted-foreground mt-2">Manage and monitor your tracked products.</p>
        </div>

        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" /> Add Product</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Track New Product</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <Label htmlFor="name">Product Name</Label>
                <Input id="name" value={newProduct.name} onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })} required />
              </div>
              <div>
                <Label htmlFor="desc">Description</Label>
                <Input id="desc" value={newProduct.description} onChange={(e) => setNewProduct({ ...newProduct, description: e.target.value })} />
              </div>
              <div>
                <Label htmlFor="url">YouTube/Reddit URL (Optional)</Label>
                <Input id="url" value={newProduct.url} onChange={(e) => setNewProduct({ ...newProduct, url: e.target.value })} />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Adding...' : 'Start Tracking'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <Card key={product.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div className="space-y-1">
                <CardTitle className="text-xl cursor-pointer hover:underline" onClick={() => navigate(`/products/${product.id}`)}>
                  {product.name}
                </CardTitle>
                <CardDescription className="line-clamp-1">{product.description || "No description"}</CardDescription>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="h-8 w-8 p-0"><MoreVertical className="h-4 w-4" /></Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => navigate(`/products/${product.id}`)}>
                    <ExternalLink className="mr-2 h-4 w-4" /> View Dashboard
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => scrapeMutation.mutate(product.name)}>
                    <RefreshCw className="mr-2 h-4 w-4" /> Scrape Now
                  </DropdownMenuItem>
                  <DropdownMenuItem className="text-red-600" onClick={() => deleteMutation.mutate(product.id)}>
                    <Trash2 className="mr-2 h-4 w-4" /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center mt-4">
                <Badge variant={product.status === 'active' ? 'default' : 'secondary'}>
                  {product.status}
                </Badge>
                {product.last_updated && (
                  <span className="text-xs text-muted-foreground">
                    Updated: {new Date(product.last_updated).toLocaleDateString()}
                  </span>
                )}
              </div>
              {/* Optional: Add review count here if backend sends it */}
              <div className="mt-4 text-sm font-medium">
                {/* @ts-ignore: review_count might be injected by backend runtime */}
                {product.review_count !== undefined ? `${product.review_count} Reviews` : ''}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </DashboardLayout>
  );
}
