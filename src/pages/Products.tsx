import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProducts, createProduct, deleteProduct, scrapeReddit, scrapeTwitter } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Trash2, RefreshCw, ExternalLink, MoreVertical, Twitter } from 'lucide-react';
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
  DropdownMenuSeparator,
  DropdownMenuLabel
} from "@/components/ui/dropdown-menu";
import { useNavigate } from 'react-router-dom';

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
    refetchInterval: 5000,
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

  // Scrape Mutations
  const redditMutation = useMutation({
    mutationFn: ({ name }: { name: string }) => scrapeReddit(name),
    onSuccess: () => toast({ title: 'Reddit Scraper', description: 'Job queued successfully.' })
  });

  const twitterMutation = useMutation({
    mutationFn: ({ name, id }: { name: string, id: string }) => scrapeTwitter(name, id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast({
        title: 'Twitter Scrape Complete',
        description: `Processed ${data.count || 0} tweets (Hybrid AI).`
      });
    },
    onError: () => toast({ title: 'Scrape Failed', description: 'Could not fetch tweets.', variant: 'destructive' })
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: newProduct.name,
      description: newProduct.description,
      platform: 'generic',
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
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Adding...' : 'Start Tracking'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <Card key={product.id} className="hover:shadow-lg transition-shadow group">
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
                  <DropdownMenuLabel>Actions</DropdownMenuLabel>
                  <DropdownMenuItem onClick={() => navigate(`/products/${product.id}`)}>
                    <ExternalLink className="mr-2 h-4 w-4" /> View Dashboard
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel>Live Data Sources</DropdownMenuLabel>
                  <DropdownMenuItem onClick={() => redditMutation.mutate({ name: product.name })}>
                    <RefreshCw className="mr-2 h-4 w-4" /> Scrape Reddit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => twitterMutation.mutate({ name: product.name, id: product.id })}>
                    <Twitter className="mr-2 h-4 w-4 text-blue-400" /> Scrape Twitter (AI)
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
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
                {/* @ts-ignore */}
                {product.review_count !== undefined && (
                  <span className="text-xs font-medium bg-muted px-2 py-1 rounded">
                    {/* @ts-ignore */}
                    {product.review_count} reviews
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </DashboardLayout>
  );
}
