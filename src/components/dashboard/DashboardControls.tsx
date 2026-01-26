import React, { useRef, useState } from 'react';
import { Upload, FileUp, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DateRangePicker } from './DateRangePicker';
import { ExportButton } from './ExportButton';
import { toast } from "sonner";
import { useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useQuery } from '@tanstack/react-query';
import { getProducts } from '@/lib/api';

const CSVUploadButton = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: products } = useQuery({ queryKey: ['products'], queryFn: getProducts });

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedProduct) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('product_id', selectedProduct);
    formData.append('platform', 'csv_import');

    try {
      // Direct fetch to backend
      const res = await fetch('http://localhost:8000/api/reviews/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) throw new Error("Upload failed");
      
      const data = await res.json();
      
      toast.success("Import Successful", {
        description: data.data?.message || "Reviews imported successfully"
      });
      
      // Refresh dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      setIsOpen(false);
    } catch (error) {
      toast.error("Import Failed", {
        description: "Could not process CSV file."
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Upload className="h-4 w-4" />
          Import CSV
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import Reviews CSV</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Product Target</label>
            <div className="max-h-40 overflow-y-auto border rounded-md p-2">
              {products?.map((p: any) => (
                <div 
                  key={p.id} 
                  className={`p-2 rounded cursor-pointer flex justify-between items-center ${selectedProduct === p.id ? 'bg-primary/10 border-primary border' : 'hover:bg-accent'}`}
                  onClick={() => setSelectedProduct(p.id)}
                >
                  <span className="font-medium">{p.name}</span>
                  {selectedProduct === p.id && <Check className="h-4 w-4 text-primary" />}
                </div>
              ))}
              {(!products || products.length === 0) && <p className="text-sm text-muted-foreground p-2">No products found.</p>}
            </div>
          </div>
          
          <div className="pt-2">
             <Button 
               className="w-full relative" 
               disabled={!selectedProduct || isUploading}
               onClick={() => fileInputRef.current?.click()}
             >
               {isUploading ? (
                 <>
                   <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                   Processing...
                 </>
               ) : (
                 <>
                   <FileUp className="mr-2 h-4 w-4" />
                   Select CSV & Upload
                 </>
               )}
             </Button>
             <input 
               type="file" 
               accept=".csv" 
               className="hidden" 
               ref={fileInputRef} 
               onChange={handleFileChange}
             />
          </div>
          <p className="text-xs text-muted-foreground text-center">
            Format: Column "text" or "content" required.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export const DashboardControls = () => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 bg-background/50 p-2 rounded-lg border backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <DateRangePicker />
      </div>
      <div className="flex items-center gap-2">
        <CSVUploadButton />
        <ExportButton />
      </div>
    </div>
  );
};
